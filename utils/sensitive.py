#!/usr/bin/env python

"""
Filter out tweets or retweets that Twitter thinks are sensitive (mostly porn).
"""

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    if 'possibly_sensitive' in tweet and tweet['possibly_sensitive']:
        pass
    elif 'retweeted_status' in tweet and 'possibly_sensitive' in tweet['retweeted_status'] and tweet['retweeted_status']['possibly_sensitive']:
        pass
    else:
        print json.dumps(tweet)



