#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    user = tweet["user"]["screen_name"]
    for mention in tweet["entities"]["user_mentions"]:
    	print ("%s %s %s" % (user, "mentions", mention["screen_name"])).encode('utf-8')
    if "retweeted_status" in tweet:
    	retweet = tweet["retweeted_status"]["user"]["screen_name"]
    	print ("%s %s %s" % (user, "retweets", retweet)).encode('utf-8')
    	