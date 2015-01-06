#!/usr/bin/env python

import sys
import json
import twarc

tweet_id = sys.argv[1]
tw = twarc.TwitterClient()
tweet = tw.fetch('https://api.twitter.com/1.1/statuses/show/%s.json' % tweet_id)

print json.dumps(tweet, indent=2)







