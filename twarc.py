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
    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--search", dest="search", action="store",
                        help="search for tweets matching a query")
    parser.add_argument("--max_id", dest="max_id", action="store",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id", action="store",
                        help="smallest id to search for")
    parser.add_argument("--stream", dest="stream", action="store",
                        help="stream tweets matching filter")
    parser.add_argument("--hydrate", dest="hydrate", action="store",
                        help="rehydrate tweets from a file of tweet ids")
    parser.add_argument("--log", dest="log", action="store",
                        default="twarc.log", help="log file")
    parser.add_argument("--consumer_key", action="store",
                        default=None, help="Twitter API consumer key")
    parser.add_argument("--consumer_secret", action="store",
                        default=None, help="Twitter API consumer secret")
    parser.add_argument("--access_token", action="store",
                        default=None, help="Twitter API access key")
    parser.add_argument("--access_token_secret", action="store",
                        default=None, help="Twitter API access token secret")
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    consumer_key = args.consumer_key or os.environ.get('CONSUMER_KEY')
    consumer_secret = args.consumer_secret or os.environ.get('CONSUMER_SECRET')
    access_token = args.access_token or os.environ.get('ACCESS_TOKEN')
    access_token_secret = args.access_token_secret or os.environ.get("ACCESS_TOKEN_SECRET")

    if not (consumer_key and consumer_secret and access_token and access_token_secret):
        raise argparse.ArgumentTypeError("Please make sure to use command line arguments to set the Twitter API keys or set the CONSUMER_KEY, CONSUMER_SECRET ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment variables")

    t = Twarc(consumer_key=consumer_key,
              consumer_secret=consumer_secret,
              access_token=access_token,
              access_token_secret=access_token_secret)

    if args.search:
        tweets = t.search(
            args.search, 
            since_id=args.since_id, 
            max_id=args.max_id
        )
    elif args.stream:
        tweets = t.stream(args.stream)
    elif args.hydrate:
        tweets = t.hydrate(open(args.hydrate))
    else:
        raise argparse.ArgumentTypeError("must supply one of: --search --stream or --hydrate")

    # iterate through the tweets and write them to stdout
    for tweet in tweets:
        logging.info("archived %s", tweet["id_str"])
        print(json.dumps(tweet))


def rate_limit(f):
    """
    A decorator to handle rate limiting from the Twitter API. If 
    a rate limit error is encountered we will sleep until we can
    issue the API call again.
    """
    def new_f(*args, **kwargs):
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                reset = int(resp.headers['x-rate-limit-reset'])
                now = time.time()
                seconds = reset - now + 10
                if seconds < 1: 
                    seconds = 10
                logging.warn("rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            elif resp.status_code == 503:
                seconds = 60
                logging.warn("503 from Twitter API, sleeping %s", seconds)
                time.sleep(seconds)
            else:
                resp.raise_for_status()
    return new_f


class Twarc(object):
    """
    Your friendly neighborhood Twitter archiving class. Twarc allows
    you to search for existing tweets, stream live tweets that match
    a filter query and lookup (hdyrate) a list of tweet ids. 
    
    Each method search, stream and hydrate returns a tweet iterator which allows
    you to do what you want with the data. Twarc handles rate limiting in the 
    API, so it will go to sleep when Twitter tells it to, and wake back up
    when it is able to get more data from the API.
    """

    def __init__(self, consumer_key, consumer_secret, access_token,
            access_token_secret):
        """
        Instantiate a Twarc instance. Make sure your environment variables
        are set.
        """

        # create our http client
        self.client = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )


    def search(self, q, max_id=None, since_id=None):
        """
        Pass in a query with optional max_id and min_id and get back 
        an iterator for decoded tweets.
        """
        logging.info("starting search for %s", q)
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
           
            resp = self.get(url, params=params)
            statuses = resp.json()["statuses"]

            if len(statuses) == 0:
                logging.info("no new tweets matching %s", params)
                break

            for status in statuses:
                yield status

            max_id = status["id_str"]


    def stream(self, query):
        """
        Returns an iterator for tweets that match a given filter query from
        the livestream of tweets happening right now.
        """
        url = 'https://stream.twitter.com/1.1/statuses/filter.json'
        params = {"track": query}
        headers = {'accept-encoding': 'deflate, gzip'}
        while True:
            logging.info("connecting to filter stream for %s", query)
            resp = self.post(url, params, headers=headers, stream=True)
            for line in resp.iter_lines(chunk_size=512):
                try:
                    yield json.loads(line.decode())
                except Exception as e:
                    logging.error("json parse error: %s - %s", e, line)


    def hydrate(self, iterator):
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
                logging.info("hydrating %s ids", len(ids))
                resp = self.post(url, data={"id": ','.join(ids)})
                tweets = resp.json()
                tweets.sort(key=lambda t: t['id_str'])
                for tweet in tweets:
                    yield tweet
                ids = []

        # hydrate any remaining ones
        if len(ids) > 0:
            logging.info("hydrating %s", ids)
            resp = self.client.post(url, data={"id": ','.join(ids)})
            for tweet in resp.json():
                yield tweet


    @rate_limit
    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)


    @rate_limit
    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs)


if __name__ == "__main__":
    main()
