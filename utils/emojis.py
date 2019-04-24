#!/usr/bin/env python3

import re
import json
import fileinput
import collections

import emoji

counts = collections.Counter()

EMOJI_RE = emoji.get_emoji_regexp()

for line in fileinput.input():
    tweet = json.loads(line)
    if 'full_text' in tweet:
        text = tweet['full_text']
    else:
        text = tweet['text']
    for char in EMOJI_RE.findall(text):
        counts[char] += 1

for char, count in counts.most_common():
    print("%s %5i" % (char, count))
