#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput

counts = {}
for line in fileinput.input():
    try:
        tweet = json.loads(line)
    except:
        continue

    for tag in tweet['entities']['hashtags']:
        t = tag['text'].lower()
        counts[t] = counts.get(t, 0) + 1

tags = counts.keys()
tags.sort(lambda a, b: cmp(counts[b], counts[a]))

for tag in tags:
    print(tag.encode('utf8'), counts[tag])
