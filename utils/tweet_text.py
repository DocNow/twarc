#!/usr/bin/env python

"""
Given a JSON file, return just the text of the tweet.
Example usage:
utils/tweet_text.py tweets.jsonl > tweets.txt
"""

from __future__ import print_function
import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)

    if 'full_text' in tweet:
        print(tweet['full_text'].encode('utf8'))
    else:
        print(tweet['text'].encode('utf8'))
