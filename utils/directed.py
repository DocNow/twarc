#!/usr/bin/env python

import json
import fileinput
import math


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
    if "retweeted_status" in tweet:
    	source = tweet["user"]["screen_name"]
    	if not source in links:
    		links[source] = {}
    	sourcelink = links[source]
    	target = tweet["retweeted_status"]["user"]["screen_name"]
    	if target in sourcelink:
    		sourcelink[target] = sourcelink[target] + 1;
    	else:
    		sourcelink[target] = 1;



linksoutput = []
for source in links.iterkeys():
	for target in links[source].iterkeys():
		value = links[source][target]
		if value >= threshold:
			linksoutput.append({"source": target, "target": source, "value": value, "type": "suit"})


print json.dumps(linksoutput)
