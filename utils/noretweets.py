#!/usr/bin/env python
"""
Given a JSON file, remove any retweets.

Example usage:
utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl
"""
from __future__ import print_function
import json
import fileinput
from collections import OrderedDict

seen = OrderedDict()
for line in fileinput.input():
    tweet = json.loads(line)

    if not 'retweeted_status' in tweet:
        id = tweet['id']
        seen[id] = tweet

for tweet in seen.values():
    print(json.dumps(tweet))

# End of file
