#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput
import collections

counts = collections.Counter()
for line in fileinput.input():
    tweet = json.loads(line)
    for tag in tweet['entities']['hashtags']:
        t = tag['text'].lower()
        counts[t] += 1

for tag, count in counts.most_common():
    print("%5i %s" % (count, tag))
