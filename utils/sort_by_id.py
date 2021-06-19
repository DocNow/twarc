#!/usr/bin/env python
"""
Sort tweets by ID.

Twitter IDs are generated in chronologically ascending order,
so this is the same as sorting by date.

Example usage:
utils/sort_by_id.py tweets.jsonl > sorted.jsonl
"""
from __future__ import print_function

import json
from operator import itemgetter
import fileinput


tweets = []
for line in fileinput.input():
    tweet = json.loads(line)
    tweets.append(tweet)

tweets = sorted(tweets, key=itemgetter("id"))

for tweet in tweets:
    print(json.dumps(tweet))

# End of file
