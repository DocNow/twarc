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

def main():
    """
    The twarc command line.
    """
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
    parser.add_argument("--filter", dest="filter", action="store_true",
                        help="filter current tweets")
    parser.add_argument("--hydrate", dest="hydrate", action="store",
                        help="rehydrate tweets from a file of tweet ids")

    args = parser.parse_args()
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


class Twarc(object):
    """
    Your friendly neighborhood Twitter archiving class. Twarc allows
    you to search for existing tweets, filter the livestream and lookup
    (hdyrate) a list of tweet ids. 
    
    Each method search, filter and lookup returns a tweet iterator which allows
    you to do what you want with the data. Twarc handles rate limiting in the 
    API, so it will go to sleep when Twitter tells it to, and wake back up
    when it is able to get more data from the API.
    """

    def __init__(self):
        """
        Instantiate a Twarc instance. Make sure your environment variables
        are set.
        """
        # TODO: allow keys to be passed in?
        ck = os.environ.get('CONSUMER_KEY')
        cks = os.environ.get('CONSUMER_SECRET')
        at = os.environ.get('ACCESS_TOKEN')
        ats = os.environ.get("ACCESS_TOKEN_SECRET")
        if not (ck and cks and at and ats):
            raise argparse.ArgumentTypeError("Please make sure CONSUMER_KEY, CONSUMER_SECRET ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment variables are set.")

        # create our http client
        self.client = OAuth1Session(
            ck,
            client_secret=cks,
            resource_owner_key=at,
            resource_owner_secret=ats
        )


    def search(self, q, max_id=None, since_id=None):
        """
        Pass in a query with optional max_id and min_id and get back 
        an iterator for decoded tweets.
        """
        url = "https://api.twitter.com/1.1/search/tweets.json"
        params = {
            "count": 100,
            "q": q
        }

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id
            
            resp = self.client.get(url, params=params)
            statuses = resp.json()["statuses"]

            if len(statuses) == 0:
                logging.info("no new tweets matching %s", params)
                break

            for status in statuses:
                yield status

            max_id = status["id_str"]


    def filter(self, query):
        """
        Returns an iterator for tweets that match a given filter query from
        the livestream of tweets happening right now.
        """
        logging.info("starting stream filter for %s", query)
        url = 'https://stream.twitter.com/1.1/statuses/filter.json'
        params = {"track": query}
        headers = {'accept-encoding': 'deflate, gzip'}
        while True:
            logging.info("connecting to filter stream for %s", query)
            r = self.client.post(url, params, headers=headers, stream=True)
            for line in r.iter_lines():
                try:
                    yield json.loads(line)
                except Exception as e:
                    logging.error("json parse error: %s - %s", e, line)


    def lookup(self, iterator):
        """
        Pass in an iterator of tweet ids and get back an iterator for the 
        decoded JSON for each corresponding tweet.
        """
        ids = []
        url = "https://api.twitter.com/1.1/statuses/lookup.json"

        # lookup 100 tweets at a time
        for tweet_id in iterator:
            tweet_id = tweet_id.strip() # remove new line if present
            ids.append(tweet_id)
            if len(ids) == 100:
                resp = self.client.post(url, data={"id": ','.join(ids)})
                for tweet in resp.json():
                    yield tweet
                ids = []

        # hydrate any remaining ones
        if len(ids) > 0:
            resp = self.client.post(url, data={"id": ','.join(ids)})
            for tweet in resp.json():
                yield tweet


    def _get_limits(self, response):
        reset = int(response.headers['x-rate-limit-reset'])
        remaining = int(response.headers['x-rate-limit-remaining'])
        return reset, remaining


if __name__ == "__main__":
    main()

