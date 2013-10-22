#!/usr/bin/env python

import os
import sys
import json
import math
import re
import fileinput

# parse command-line args
mode="retweets"
# if args include --mode, get mode and remove first two args, leaving file name(s) (if any) in args
if len(sys.argv) > 1:
	if sys.argv[1] == "--mode":
		mode=sys.argv[2]
		del sys.argv[0]
		del sys.argv[0]

threshold = 1
links = {}
users = {}

def addlink(fromtoken, totoken):
    if not fromtoken in links:
    	links[fromtoken] = {}
    if not fromtoken in users:
    	users[fromtoken] = {"source": 0, "target": 1}
    else:
    	users[fromtoken]["target"] = users[fromtoken]["target"] + 1
    userlink = links[fromtoken]
    if totoken in userlink:
    	userlink[totoken] = userlink[totoken] + 1;
    else:
    	userlink[totoken] = 1;
    if totoken in users:
    	users[totoken]["source"] = users[totoken]["source"] + 1
    else:
    	users[totoken] = {"source": 1, "target": 0}



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
    if mode == 'mentions':
	    if "user_mentions" in tweet["entities"]:
		    for mention in tweet["entities"]["user_mentions"]:
	    		mentionuser = str(mention["screen_name"])
	    		addlink(source, mentionuser)
    elif mode == 'replies':
    	if not(tweet["in_reply_to_screen_name"] == None):
    		addlink(tweet["in_reply_to_screen_name"], source)
    else: # default mode: retweets
	    if "retweeted_status" in tweet:
    		addlink(source, tweet["retweeted_status"]["user"]["screen_name"])

# generate nodes json
nodesoutput = []
usernames = []
for u in users.iterkeys():
	node = users[u]
	usernames.append(u)
	nodesoutput.append({"name": u, "title": str(u + " (" + str(node["source"]) + "/" + str(node["target"]) + ")")})
	
nodes = json.dumps(nodesoutput)

# generate links json
linksoutput = []
for source in links.iterkeys():
	for target in links[source].iterkeys():
		value = links[source][target]
		if value >= threshold:
			linksoutput.append({"source": usernames.index(target), "target": usernames.index(source), "value": value})

links = json.dumps(linksoutput)

# generate html by replacing token
template_file = os.path.join(os.path.dirname(__file__), "templates", "directed.html")
with open (template_file, "r") as template:
	print template.read().replace('$LINKS$', links).replace('$NODES$', nodes).replace('$MODE$', mode)
