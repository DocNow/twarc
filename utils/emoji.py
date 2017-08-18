#!/usr/bin/env python3

import re
import json
import fileinput
import collections

regex = re.compile(r'\d+(.*?)(?:\u263a|\U0001f645)')
counts = collections.Counter()

for line in fileinput.input():
    tweet = json.loads(line)
    if 'full_text' in tweet:
        text = tweet['full_text']
    else:
        text = tweet['text']
    for char in re.findall(u'[\U0001f600-\U0001f650]', text):
        counts[char] += 1

for char, count in counts.most_common():
    print("%s %5i" % (char, count))


