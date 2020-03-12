#!/usr/bin/env python3

import re
import json
import fileinput
import collections
import optparse

import emoji

opt_parser = optparse.OptionParser()

opt_parser.add_option(
    "-n",
    "--number",
    dest="number",
    type="int",
    default= 10
)
options, args = opt_parser.parse_args()
tweets = args

number_of_emojis = options.number
tweets = tweets.pop()

counts = collections.Counter()

EMOJI_RE = emoji.get_emoji_regexp()

for line in open(tweets):
    tweet = json.loads(line)
    if 'full_text' in tweet:
        text = tweet['full_text']
    else:
        text = tweet['text']
    for char in EMOJI_RE.findall(text):
        counts[char] += 1

for char, count in counts.most_common(number_of_emojis):
    print("%s %5i" % (char, count))
