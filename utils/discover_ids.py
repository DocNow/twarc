#!/usr/bin/env python

"""
This is an imperfect way of discovering tweet ids that match a particular
query using the infinite scroll windown on Twitter's website. It doesn't
yield complete or quick results; so really it can only be used for smallish
queries. Once you have the tweet ids for a given query you can hydrate
them with twarc.py. For example:

    discover_ids.py '#code4lib' > ids.txt
    twarc.py --hydrate ids.txt > tweets.jsonl

"""
from __future__ import print_function

import re
import json
import time
import random
import logging
import argparse
import calendar
import requests


def main():
    parser = argparse.ArgumentParser("discover_ids")
    parser.add_argument("query", action="store",
                        help="tweets to search for")
    args = parser.parse_args()

    logging.basicConfig(filename="discover.log", level=logging.INFO)
    for id in discover_ids(args.query):
        print(id)

def discover_ids(query):
    cursor = None
    url = 'https://twitter.com/i/search/timeline?'
    q = {
        "q": query,
        'f': 'realtime',
        "src": "typd",
        "include_available_features": 1,
        "include_entities": 1,
        "oldest_unread_id": 0
    }

    while True:
        logging.info("collecting tweet ids with cursor=%s", cursor)
        q["last_note_ts"] = calendar.timegm(time.gmtime())
        if cursor:
            q["scroll_cursor"] = cursor

        r = requests.get(url, headers={"user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36"}, params=q)
        s = json.loads(r.content)

        html = s["items_html"]
        tweet_ids = re.findall(r'<a href=\"/.+/status/(\d+)', html)
        logging.info("discovered tweet ids: %s", tweet_ids)

        if len(tweet_ids) == 0:
            logging.debug("no more tweet ids: %s", html)
            raise StopIteration

        for tweet_id in tweet_ids:
            yield tweet_id

        # seems to fetch more tweets when we sleep a random amount of time?
        seconds = random.randint(3, 8)
        logging.debug("sleeping for %s" % seconds)
        time.sleep(seconds)

        cursor = s['scroll_cursor']

if __name__ == "__main__":
    main()
