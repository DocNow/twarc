#!/usr/bin/env python

from __future__ import print_function
import os
import re
import sys
import json
import time
import logging
import argparse
import requests
from requests_oauthlib import OAuth1Session

try:
    # Python 3
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import quote
    from urllib import urlencode


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
            print("Please make sure CONSUMER_KEY, CONSUMER_SECRET, "
                  "ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment "
                  "variables are set.")
            sys.exit(1)

        self.client = OAuth1Session(
            ck,
            client_secret=cks,
            resource_owner_key=at,
            resource_owner_secret=ats
        )

        self.remaining = {'search': 0, 'lookup': 0}
        self.reset = {'search': None, 'lookup': None}

        self.ping()

    def fetch(self, url, tries=5):
        logging.debug("fetching %s", url)
        if tries == 0:
            msg = "unable to fetch %s - too many tries!" % url
            logging.error(msg)
            raise Exception(msg)

        time.sleep(1)
        self.check_search()
        try:
            resp = self.client.get(url)

            if resp.status_code == 200:
                return resp.json()

            secs = (6 - tries) * 2
            logging.error("got error when fetching %s sleeping %s secs: %s", url, secs, resp)
            time.sleep(secs)

            return self.fetch(url, tries - 1)

        except Exception as e:
            logging.error("unable to fetch %s: %s", url, e)
            return self.fetch(url, tries - 1)

    def hydrate(self, ids):
        self.check_lookup()
        url = "https://api.twitter.com/1.1/statuses/lookup.json"
        ids = ','.join(ids)
        logging.info("hydrating: %s", ids)
        resp = self.client.post(url, data={"id": ids})
        for tweet in resp.json():
            yield tweet

    def check_search(self):
        """
        Blocks until Twitter API allows us to search.
        """
        return self.check('search')

    def check_lookup(self):
        """
        Blocks until Twitter API allows us to lookup tweets.
        """
        return self.check('lookup')

    def check(self, resource_type):
        """
        Blocks until Twitter quota allows for API calls, or returns
        immediately if we're able to make calls.
        """
        if resource_type not in ["search", "lookup"]:
            raise Exception("unknown resource type: %s", resource_type)
        remaining = self.remaining[resource_type]
        reset = self.reset[resource_type]

        logging.info("%s rate limit remaining %s", resource_type, remaining)
        while remaining <= 1:
            now = time.time()
            logging.debug("rate limit < 1, now=%s and reset=%s", now, reset)
            if reset and now < reset:
                # padded with 5 seconds just to be on the safe side
                secs = reset - now + 5
                logging.info("sleeping %s for %s limit", secs, resource_type)
                time.sleep(secs)
            else:
                # sleep a second before checking again for new rate limit
                time.sleep(1)
            # get the latest limit
            self.ping()

        self.remaining[resource_type] -= 1

    def ping(self, times=10):
        """fetches latest rate limits from Twitter
        """
        logging.debug("checking for rate limit info")
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json?resources=search,statuses"
        response = self.client.get(url)
        result = response.json()

        if "resources" in result:
            self.reset['search'] = int(result["resources"]["search"]["/search/tweets"]["reset"])
            self.remaining['search'] = int(result["resources"]["search"]["/search/tweets"]["remaining"])
            self.reset['lookup'] = int(result["resources"]["statuses"]["/statuses/lookup"]["reset"])
            self.remaining['lookup'] = int(result["resources"]["statuses"]["/statuses/lookup"]["remaining"])
        else:
            logging.error("unable to fetch rate limits")
            if times == 0:
                logging.error("ping isn't working :(")
                raise Exception("unable to ping")
            else:
                times -= 1
                time.sleep(1)
                logging.info("trying to ping again: %s", times)
                return self.ping(times)

        logging.info("new rate limits: search: %s/%s ; lookup: %s/%s",
                self.remaining['search'], self.reset['search'],
                self.remaining['lookup'], self.reset['lookup'])


def search(q, since_id=None, max_id=None, only_ids=False):
    """returns a generator for *all* search results. 
    """
    logging.info("starting search for %s with since_id=%s and max_id=%s" %
                 (q, since_id, max_id))
    while True:
        results, max_id = search_result(q, since_id, max_id)
        if len(results) == 0:
            break
        for status in results:
            yield status


def stream(q):
    """Will return a generator for tweets that match a given query from
    the livestream.
    """
    logging.info("starting stream filter for %s", q)
    client = TwitterClient()

    url = 'https://stream.twitter.com/1.1/statuses/filter.json'
    params = {"track": q}
    headers = {'accept-encoding': 'deflate, gzip'}
    while True:
        logging.info("connecting to filter stream for %s", q)
        r = client.client.post(url, params, headers=headers, stream=True)
        for line in r.iter_lines():
            try:
                yield json.loads(line)
            except Exception as e:
                logging.error("json parse error: %s - %s", e, line)


def search_result(q, since_id=None, max_id=None):
    """returns a single page of search results
    """
    client = TwitterClient()
    url = ("https://api.twitter.com/1.1/search/tweets.json?count=100&q=%s" %
           quote(q, safe=''))
    if since_id:
        url += "&since_id=%s" % since_id
    if max_id:
        url += "&max_id=%s" % max_id
    resp = client.fetch(url)

    statuses = resp["statuses"]

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
        if re.match("^%s-\d+\.json$" % quote(q, safe=''), filename):
            other_archive_files.append(filename)
    other_archive_files.sort()
    while len(other_archive_files) != 0:
        f = other_archive_files.pop()
        if os.path.getsize(f) > 0:
            return f
    return None


def archive(q, statuses):
    t = time.strftime("%Y%m%d%H%M%S", time.localtime())
    archive_filename = "%s-%s.json" % (quote(q, safe=''), t)
    logging.info("writing tweets to %s" % archive_filename)

    fh = open(archive_filename, "w")
    for status in statuses:
        try:
            logging.info("archived %s", status["id_str"])
            fh.write(json.dumps(status))
            fh.write("\n")
        except Exception, e:
            logging.exception("unable to archive status: %s", status)


def hydrate(tweet_ids):
    """
    Give hydrate a list or generator of Twitter IDs and you get back 
    a generator of line-oriented JSON for the rehydrated data.
    """
    ids = []
    client = TwitterClient()

    # rehydrate every 100 twitter IDs with one request
    for tweet_id in tweet_ids:
        tweet_id = tweet_id.strip() # remove new line if present
        ids.append(tweet_id)
        if len(ids) == 100:
            for tweet in client.hydrate(ids):
                yield tweet
            ids = []

    # hydrate remaining ones
    if len(ids) > 0:
        for tweet in client.hydrate(ids):
            yield tweet


if __name__ == "__main__":
    logging.basicConfig(
        filename="twarc.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--query", dest="query", action="store",
                        help="query to use to filter Twitter results")
    parser.add_argument("--max_id", dest="max_id", action="store",
                        help="maximum tweet id to fetch")
    parser.add_argument("--since_id", dest="since_id", action="store",
                        help="smallest id to fetch")
    parser.add_argument("--stream", dest="stream", action="store_true",
                        help="stream current tweets instead of doing a search")
    parser.add_argument("--hydrate", dest="hydrate", action="store",
                        help="rehydrate tweets from a file of tweet ids")

    args = parser.parse_args()

    if args.query is None and args.hydrate is None:
        parser.print_usage()
        sys.exit(1)

    if args.stream:
        tweets = stream(args.query)
    elif args.hydrate:
        tweets = hydrate(open(args.hydrate))
    else:
        if args.since_id:
            since_id = args.since_id
        else:
            since_id = most_recent_id(args.query)
        tweets = search(
            args.query,
            since_id=since_id,
            max_id=args.max_id,
        )

    # TODO: add option to control where the data goes

    if args.query:
        archive(args.query, tweets)
    else:
        for tweet in tweets:
            print(json.dumps(tweet))
