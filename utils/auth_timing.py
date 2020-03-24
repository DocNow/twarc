#!/usr/bin/env python3

"""
Twitter's rate limits allow App Auth contexts to search at 450 requests
every 15 minutes, and User Auth contexts at 180 requests per 15 minutes. 
This script exercises both contexts and counts how tweets it is able to 
receive. We should see a significant number more tweets coming back for App
Auth.

Typical output should look like:

    app auth:  44999
    user auth:  18000

https://developer.twitter.com/en/docs/basics/rate-limits
"""

import logging
from twarc import Twarc
from datetime import datetime
from datetime import timedelta

logging.basicConfig(
    filename='time_test.log',
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def count_tweets(app_auth):
    """
    Search for covid_19 in tweets using the given context and return the number
    of tweets that were fetched in 10 minutes.
    """
    count = 0
    t = Twarc(app_auth=app_auth)
    start = None
    for tweet in t.search('covid_19'):
        # start the timer when we get the first tweet
        if start is None:
            start = datetime.now()
        count += 1
        if datetime.now() - start > timedelta(minutes=10):
            break
    t.client.close()
    return count

print('app auth: ', count_tweets(app_auth=True))
print('user auth: ', count_tweets(app_auth=False))
