#!/usr/bin/env python

"""
Filter tweets/retweets that have geocoding.
"""
from __future__ import print_function

import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)
    if 'retweeted_status' in tweet:
        if tweet['retweeted_status']['geo']:
            print(json.dumps(tweet))
    elif tweet['geo']:
        print(json.dumps(tweet))
