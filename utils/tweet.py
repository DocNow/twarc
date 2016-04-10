#!/usr/bin/env python

"""
Fetch a single tweet as JSON using its id.
"""
from __future__ import print_function

import os
import json
import twarc
import argparse

e = os.environ.get
parser = argparse.ArgumentParser("tweet.py")

parser.add_argument('tweet_id', action="store", help="Tweet ID")
parser.add_argument("--consumer_key", action="store",
                    default=e('CONSUMER_KEY'),
                    help="Twitter API consumer key")
parser.add_argument("--consumer_secret", action="store",
                    default=e('CONSUMER_SECRET'),
                    help="Twitter API consumer secret")
parser.add_argument("--access_token", action="store",
                    default=e('ACCESS_TOKEN'),
                    help="Twitter API access key")
parser.add_argument("--access_token_secret", action="store",
                    default=e('ACCESS_TOKEN_SECRET'),
                    help="Twitter API access token secret")
args = parser.parse_args()

tw = twarc.Twarc(args.consumer_key, args.consumer_secret, args.access_token, args.access_token_secret)
tweet = tw.get('https://api.twitter.com/1.1/statuses/show/%s.json' % args.tweet_id)

print(json.dumps(tweet.json(), indent=2))
