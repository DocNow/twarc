#!/usr/bin/env python

import json
import fileinput
import math
import sys

# parse command-line args
mode="retweets"
# if args include -m, get mode and remove first two args, leaving file name(s) (if any) in args
if len(sys.argv) > 1:
	if sys.argv[1] == "-m":
		mode=sys.argv[2]
		del sys.argv[0]
		del sys.argv[0]

nodes = [];
links = {};


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
    user = tweet["user"]["screen_name"]
    if not user in nodes:
    	nodes.append(user)
    if not user in links:
    	links[user] = {}
    userlink = links[user]
    if mode == 'mentions':
	    if "user_mentions" in tweet["entities"]:
		    for mention in tweet["entities"]["user_mentions"]:
	    		mentionuser = str(mention["screen_name"])
    			if not mentionuser in nodes:
    				nodes.append(mentionuser)
	    		if mentionuser in userlink:
    				userlink[mentionuser] = userlink[mentionuser] + 1;
    			else:
    				userlink[mentionuser] = 1;
    else:
	    if "retweeted_status" in tweet:
    		retweet = tweet["retweeted_status"]["user"]["screen_name"]
    		if not retweet in nodes:
    			nodes.append(retweet)
	    	if retweet in userlink:
    			userlink[retweet] = userlink[retweet] + 1;
    		else:
    			userlink[retweet] = 1;

maxlinks = 0

nodecounts = {}
for node in nodes:
	nodecounts[node] = 0;

linksoutput = []
for subject in links.iterkeys():
	for object in links[subject].iterkeys():
		strength = links[subject][object]
		linksoutput.append({"source": nodes.index(subject), "target": nodes.index(object), "value": strength})
		nodecounts[subject] = nodecounts[subject] + strength
		nodecounts[object] = nodecounts[object] + strength
		if nodecounts[subject] > maxlinks:
			maxlinks = nodecounts[subject]
		if nodecounts[object] > maxlinks:
			maxlinks = nodecounts[object]

#print json.dumps(nodecounts)

nodesoutput = []
for node in nodes:
	nodesoutput.append({"name": node, "group": int(round(nodecounts[node]/maxlinks * 8))})
	
	
nodes = json.dumps(nodesoutput)
links = json.dumps(linksoutput)

# generate html by replacing token
with open ("resources/rels.html", "r") as template:
	print template.read().replace('$LINKS$', links).replace('$NODES$', nodes)

