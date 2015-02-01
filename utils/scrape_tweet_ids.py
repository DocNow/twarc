#!/usr/bin/env python

"""
This is just an imperfect way of discovering tweet ids that match 
a particular query by using the Twitter website. It isn't complete 
or quick, and really can only be used for smallish queries.
"""

import re
import json
import time
import random
import logging
import argparse
import calendar
import requests


def main():
    parser = argparse.ArgumentParser("scrape_tweet_ids")
    parser.add_argument("query", action="store",
                        help="tweets to search for")
    args = parser.parse_args()

    logging.basicConfig(filename="scrape.log", level=logging.INFO)
    for id in scrape_tweet_ids(args.query):
        print id

def scrape_tweet_ids(query):
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
        logging.info("scraping tweets with curor=%s", cursor)
        q["last_note_ts"] = calendar.timegm(time.gmtime())
        if cursor:
            q["scroll_cursor"] = cursor

        r = requests.get(url, headers={"user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36"}, params=q)
        s = json.loads(r.content)

        html = s["items_html"]
        tweet_ids = re.findall(r'<a href=\"/.+/status/(\d+)', html)
        logging.info("scraped tweet ids: %s", tweet_ids)

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
