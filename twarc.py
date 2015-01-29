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
            raise argparse.ArgumentTypeError("Please make sure CONSUMER_KEY, CONSUMER_SECRET ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment variables are set.")

        self.client = OAuth1Session(
            ck,
            client_secret=cks,
            resource_owner_key=at,
            resource_owner_secret=ats
        )

        self.search_remaining = 0
        self.search_reset = None
        self.lookup_remaining = 0
        self.lookup_reset = None

    def search(self, query, max_id=None, min_id=None):
        pass

    def filter(self, query):
        pass

    def lookup(self, fh):
        pass

    def _get_limits(self, response):
        reset = int(response.headers['x-rate-limit-reset'])
        remaining = int(response.headers['x-rate-limit-remaining'])
        return reset, remaining

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
    parser.add_argument("--search", dest="search", action="store",
                        help="search for tweets matching a query")
    parser.add_argument("--max_id", dest="max_id", action="store",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id", action="store",
                        help="smallest id to search for")
    parser.add_argument("--filter", dest="stream", action="store_true",
                        help="filter current tweets")
    parser.add_argument("--hydrate", dest="hydrate", action="store",
                        help="rehydrate tweets from a file of tweet ids")

    args = parser.parse_args()

    if args.query is None and args.hydrate is None:
        parser.print_usage()
        sys.exit(1)

    t = Twarc()

    if args.search:
        tweets = t.search(
            args.search, 
            since_id=args.since_id, 
            max_id=args.max_id
        )
    elif args.filter:
        tweets = t.filter(args.filter)
    elif args.hydrate:
        tweets = t.lookup(open(args.hydrate))
    else:
        raise argparse.ArgumentTypeError("must supply one of: --search --filter or --hydrate")

    for tweet in tweets:
        print(json.dumps(tweet))
