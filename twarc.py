#!/usr/bin/env python

import os
import re
import sys
import json
import time
import config
import oauth2
import urllib
import logging
import argparse
import requests

USER_AGENT = "twarc (http://twitter.com/edsu/twarc)"

consumer = oauth2.Consumer(key=config.consumer_key, secret=config.consumer_secret)
token = oauth2.Token(config.access_token, config.access_token_secret)
client = oauth2.Client(consumer, token)


class RateLimiter:

    def __init__(self):
        self.remaining = 0
        self.reset = time.time() + 800
        self._ping()

    def check(self):
        logging.info("rate limit remaining %s" % self.remaining)
        if self.remaining <= 1:
            now = time.time()
            if now < self.reset:
                # padded with 5 seconds just to be on the safe side
                secs = self.reset - now + 5 
                logging.info("sleeping %s seconds for rate limiting" % secs)
                time.sleep(secs)
            # get the latest limit
            self._ping()
            return self.check()
        self.remaining -= 1

    def _ping(self):
        """fetches latest rate limits from Twitter
        """
        logging.info("checking for rate limit info")
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json?resources=search"
        response, content = client.request(url)
        result = json.loads(content)

        # look for limits in the json or the http headers, which can 
        # happen when we are rate limited from checking the rate limits :)

        if "resources" in result:
            self.reset = json.loads(content)["resources"]["search"]["/search/tweets"]["reset"]
            self.remaining = json.loads(content)["resources"]["search"]["/search/tweets"]["remaining"]
        else:
            self.reset = response["x-rate-limit-reset"]
            self.remaining = response["x-rate-limit-remaining"]

        logging.info("new rate limit remaining=%s and reset=%s", self.remaining, self.reset)


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
    # do the api call
    url = "https://api.twitter.com/1.1/search/tweets.json?count=100&q=%s" % urllib.quote(q)
    if since_id:
        url += "&since_id=%s" % since_id
    if max_id:
        url += "&max_id=%s" % max_id
    resp, content = fetch(url)

    statuses = json.loads(content)["statuses"]
    
    if len(statuses) > 0:
        new_max_id = int(statuses[-1]["id_str"]) + 1
    else:
        new_max_id = max_id

    if max_id == new_max_id:
        logging.info("no new tweets with id < %s", max_id)
        return [], max_id

    return statuses, new_max_id


def fetch(url, tries=5):
    logging.info("fetching %s", url)
    if tries == 0:
        logging.error("unable to fetch %s - too many tries!", url)
        sys.exit(1)

    rate_limiter.check()
    resp, content = client.request(url)

    if resp.status == 200:
        return resp, content

    secs =  (6 - tries) * 2
    logging.error("got error when fetching %s sleeping %s secs: %s - %s", url, secs, resp, content)
    time.sleep(secs)

    return fetch(url, tries - 1)


def most_recent_id(q):
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
    for tweet_id in scrape_tweet_ids(query, max_id, sleep=1):
        rate_limiter.check()
        url = "https://api.twitter.com/1.1/statuses/show.json?id=%s" % tweet_id
        resp, content = fetch(url)
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
        r = requests.get(url, params=q, headers={'User-agent': USER_AGENT})
        s = json.loads(r.content)

        html = s["items_html"]
        tweet_ids = re.findall(r'<a href=\"/.+/status/(\d+)', html)

        if len(tweet_ids) == 0:
            raise StopIteration

        for tweet_id in tweet_ids:
            yield tweet_id

        if not s['has_more_items']:
            raise StopIteration

        time.sleep(sleep)
        cursor = s['scroll_cursor']

logging.basicConfig(filename="twarc.log", level=logging.INFO)
rate_limiter = RateLimiter()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--scrape", dest="scrape", action="store_true", help='attempt to scrape tweets from search.twitter.com for tweets not available via Twitter\'s search REST API')
    parser.add_argument("--maxid", dest="maxid", action="store", help="maximum tweet id to fetch")
    parser.add_argument("query")
    args = parser.parse_args()

    since_id = most_recent_id(args.query)
    max_id = None

    archive(args.query, search(args.query, since_id=since_id, max_id=args.maxid, scrape=args.scrape))
