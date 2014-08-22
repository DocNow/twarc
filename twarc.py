#!/usr/bin/env python

import os
import re
import sys
import json
import time
import oauth2
import urllib
import logging
import argparse
import requests


class TwitterClient:
    """
    A class that manages authentication and quota management for 
    the Twitter API.
    """

    def __init__(self):
        ck = os.environ.get('CONSUMER_KEY')
        cks = os.environ.get('CONSUMER_SECRET')
        at = os.environ.get('ACCESS_TOKEN')
        ats = os.environ.get("ACCESS_TOKEN_SECRET")

        if not (ck and cks and at and ats):
            print "Please make sure CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment variables are set."
            sys.exit(1)

        consumer = oauth2.Consumer(key=ck, secret=cks)
        token = oauth2.Token(at, ats)
        self.client = oauth2.Client(consumer, token, timeout=60)

        self.remaining = 0
        self.reset = None
        self.ping()

    def fetch(self, url, tries=5):
        logging.debug("fetching %s", url)
        if tries == 0:
            msg = "unable to fetch %s - too many tries!" % url
            logging.error(msg)
            raise Exception(msg)

        time.sleep(1)
        self.check()
        try:
            resp, content = self.client.request(url)

            if resp.status == 200:
                return resp, content

            secs =  (6 - tries) * 2
            logging.error("got error when fetching %s sleeping %s secs: %s - %s", url, secs, resp, content)
            time.sleep(secs)

            return self.fetch(url, tries - 1)

        except Exception as e:
            logging.error("unable to fetch %s: %s", url, e)
            return self.fetch(url, tries - 1)

    def check(self):
        """
        Blocks until Twitter quota allows for API calls, or returns
        immediately if we're able to make calls.
        """
        logging.debug("rate limit remaining %s" % self.remaining)
        while self.remaining <= 1:
            now = time.time()
            logging.debug("rate limit < 1, now=%s and reset=%s", now, self.reset)
            if self.reset and now < self.reset:
                # padded with 5 seconds just to be on the safe side
                secs = self.reset - now + 5 
                logging.debug("sleeping %s seconds for rate limiting" % secs)
                time.sleep(secs)
            else:
                # sleep a second before checking again for new rate limit
                time.sleep(1)
            # get the latest limit
            self.ping()
        self.remaining -= 1

    def ping(self):
        """fetches latest rate limits from Twitter
        """
        logging.debug("checking for rate limit info")
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json?resources=search"
        response, content = self.client.request(url)
        result = json.loads(content)

        # look for limits in the json or the http headers, which can 
        # happen when we are rate limited from checking the rate limits :)

        if "resources" in result:
            self.reset = int(json.loads(content)["resources"]["search"]["/search/tweets"]["reset"])
            self.remaining = int(json.loads(content)["resources"]["search"]["/search/tweets"]["remaining"])
        else:
            self.reset = int(response["x-rate-limit-reset"])
            self.remaining = int(response["x-rate-limit-remaining"])

        logging.debug("new rate limit remaining=%s and reset=%s", self.remaining, self.reset)


def search(q, since_id=None, max_id=None, scrape=True, only_ids=False):
    """returns a generator for *all* search results. If you supply scrape, 
    twarc will attemp to dig back further in time by scraping search.twitter.com
    and looking up individual tweets.
    """
    logging.info("starting search for %s with since_id=%s and max_id=%s" % (q, since_id, max_id))
    while True:
        results, max_id = search_result(q, since_id, max_id)
        if len(results) == 0:
            break
        for status in results:
            yield status

    if scrape and not since_id:
        for status in scrape_tweets(q, max_id=max_id):
            yield status


def search_result(q, since_id=None, max_id=None):
    """returns a single page of search results
    """
    client = TwitterClient()
    url = "https://api.twitter.com/1.1/search/tweets.json?count=100&q=%s" % urllib.quote(q)
    if since_id:
        url += "&since_id=%s" % since_id
    if max_id:
        url += "&max_id=%s" % max_id
    resp, content = client.fetch(url)

    statuses = json.loads(content)["statuses"]
    
    if len(statuses) > 0:
        new_max_id = int(statuses[-1]["id_str"]) + 1
    else:
        new_max_id = max_id

    if max_id == new_max_id:
        logging.info("no new tweets with id < %s", max_id)
        return [], max_id

    return statuses, new_max_id

def most_recent_id(q):
    """
    infer most recent id based on snapshots available in current directory
    """
    since_id = None
    last_archive_file = last_archive(q)
    if last_archive_file:
        line = open(last_archive_file).readline()
        if line:
            since_id = json.loads(line)["id_str"]
    return since_id


def last_archive(q):
    other_archive_files = []
    for filename in os.listdir("."):
        if re.match("^%s-\d+\.json$" % q, filename):
            other_archive_files.append(filename)
    other_archive_files.sort()
    while len(other_archive_files) != 0:
        f = other_archive_files.pop()
        if os.path.getsize(f) > 0:
            return f
    return None


def archive(q, statuses):
    t = time.strftime("%Y%m%d%H%M%S", time.localtime())
    archive_filename = "%s-%s.json" % (q, t)
    logging.info("writing tweets to %s" % archive_filename)

    fh = open(archive_filename, "w")
    for status in statuses:
        url = "http://twitter.com/%s/status/%s" % (status["user"]["screen_name"], status["id_str"])
        logging.info("archived %s", url)
        fh.write(json.dumps(status))
        fh.write("\n")


def scrape_tweets(query, max_id=None, sleep=1):
    """
    A kinda sneaky and slow way to retrieve older tweets, now that search on 
    the Twitter website extends back in time.
    """
    client = TwitterClient()
    for tweet_id in scrape_tweet_ids(query, max_id, sleep=1):
        url = "https://api.twitter.com/1.1/statuses/show.json?id=%s" % tweet_id
        resp, content = client.fetch(url)
        yield json.loads(content)


def scrape_tweet_ids(query, max_id, sleep=1):
    cursor = None
    url = 'https://twitter.com/i/search/timeline?'
    q = {
        "q": query,
        'f': 'realtime',
        "include_available_features": 1,
        "include_entities": 1,
        "last_note_ts": 0,
        "oldest_unread_id": 0
    }

    while True:
        logging.info("scraping tweets with id < %s", max_id)
        if cursor:
            q["scroll_cursor"] = cursor

        logging.info("scraping %s", url + "?" + urllib.urlencode(q))
        r = requests.get(url, params=q)
        s = json.loads(r.content)

        html = s["items_html"]
        tweet_ids = re.findall(r'<a href=\"/.+/status/(\d+)', html)

        if len(tweet_ids) == 0:
            raise StopIteration

        for tweet_id in tweet_ids:
            yield tweet_id

        if not s['has_more_items']:
            raise StopIteration

        if sleep:
            time.sleep(sleep)
        cursor = s['scroll_cursor']


if __name__ == "__main__":
    logging.basicConfig(
        filename="twarc.log",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--scrape", dest="scrape", action="store_true", help='attempt to scrape tweets from search.twitter.com for tweets not available via Twitter\'s search REST API')
    parser.add_argument("--max_id", dest="max_id", action="store", help="maximum tweet id to fetch")
    parser.add_argument("--since_id", dest="since_id", action="store", help="smallest id to fetch")
    parser.add_argument("query")
    args = parser.parse_args()

    if args.since_id:
        since_id = args.since_id
    else:
        since_id = most_recent_id(args.query)

    archive(args.query, search(args.query, since_id=since_id, max_id=args.max_id, scrape=args.scrape))
