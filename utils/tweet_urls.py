#!/usr/bin/env python

"""
Used in conjunction with retweet.py.

Prints out the retweet count, and url of the retweeted tweet.

Takes in the output from retweet.py

tweet_urls.py retweets.jsonl > retweets.txt
"""
from __future__ import print_function

import sys
import json
import fileinput

for line in fileinput.input():
    try:
        tweet = json.loads(line)
        tweet_id = tweet["id_str"]
        screen_name = tweet["user"]["screen_name"]
        retweet_count = tweet["retweet_count"]
        tweet_urls = "https://twitter.com/%s/status/%s" % (screen_name,tweet_id)
        print ("%d retweets of %s" % (retweet_count, tweet_urls))
    except Exception as e:
        sys.stderr.write("uhoh: %s\n" % e)
