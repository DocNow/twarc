#!/usr/bin/env python

"""
Fetch a single tweet as JSON using its id.
"""

import sys
import json
import twarc

tweet_id = sys.argv[1]
tw = twarc.Twarc()
tweet = tw.get('https://api.twitter.com/1.1/statuses/show/%s.json' % tweet_id)

print json.dumps(tweet.json(), indent=2)







