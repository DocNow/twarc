#!/usr/bin/env python

import json
import fileinput
import math
import os, sys

# parse command-line args
mode="retweets"
# if args include -m, get mode and remove first two args, leaving file name(s) (if any) in args
if len(sys.argv) > 1:
	if sys.argv[1] == "-m":
		mode=sys.argv[2]
		del sys.argv[0]
		del sys.argv[0]

threshold = 1
links = {}


# nodes will end up as ["userA", "userB", ...]
# links will end up as 
#	{
#		"userA": {"userB": 3},
#		"userB": {"userA": 1},
#		...
#	}
#	
# Meaning that userA mentions userB 3 times, and userB mentions userA once.


for line in fileinput.input():
    tweet = json.loads(line)
    source = tweet["user"]["screen_name"]
    if not source in links:
    	links[source] = {}
    userlink = links[source]
    if mode == 'mentions':
	    if "user_mentions" in tweet["entities"]:
		    for mention in tweet["entities"]["user_mentions"]:
	    		mentionuser = str(mention["screen_name"])
	    		if mentionuser in userlink:
    				userlink[mentionuser] = userlink[mentionuser] + 1;
    			else:
    				userlink[mentionuser] = 1;
    else:
	    if "retweeted_status" in tweet:
    		target = tweet["retweeted_status"]["user"]["screen_name"]
    		if target in userlink:
    			userlink[target] = userlink[target] + 1;
    		else:
    			userlink[target] = 1;


# generate links json
linksoutput = []
for source in links.iterkeys():
	for target in links[source].iterkeys():
		value = links[source][target]
		if value >= threshold:
			linksoutput.append({"source": target, "target": source, "value": value, "type": "suit"})

links = json.dumps(linksoutput)

# generate html by replacing token
with open ("resources/directed.html", "r") as template:
	print template.read().replace('$LINKS$', links)
