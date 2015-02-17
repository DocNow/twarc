#!/usr/bin/env python

from __future__ import print_function
import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)
    if 'media' in tweet['entities']:
        for media in tweet['entities']['media']:
            print(media['media_url'])
