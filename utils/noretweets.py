#!/usr/bin/env python
"""
Given a JSON file, remove any retweets.

Example usage:
utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl
"""
from __future__ import print_function
import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)

    if not 'retweeted_status' in tweet:
        print(json.dumps(tweet))
