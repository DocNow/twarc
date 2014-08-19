#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    if 'retweeted_status' in tweet:
        if tweet['retweeted_status']['geo']:
            print json.dumps(tweet)
    elif tweet['geo']:
        print json.dumps(tweet)
