#!/usr/bin/env python

import os
import sys
import json
import math
import re
import optparse
import fileinput
import d3json # local module
import ast

opt_parser = optparse.OptionParser()
opt_parser.add_option("-m", "--mode", dest="mode", help="retweets (default) | mentions | replies",
    default='retweets')
opt_parser.add_option("-t", "--threshold", dest="threshold", type="int", 
	help="minimum links to qualify for inclusion (default: 1)", default=1)
opt_parser.add_option("-o", "--output", dest="output", type="str", 
	help="embed | json (default: embed)", default="embed")
opt_parser.add_option("-p", "--template", dest="template", type="str", 
	help="name of template in utils/template (default: directed.html)", default="directed.html")
	
opts, args = opt_parser.parse_args()

# prepare to serialize opts and args as json
# converting opts to str produces string with single quotes,
# but json requires double quotes
#optsdict = json.loads(str(opts).replace("'", '"'))
#argsdict = json.loads(str(args).replace("'", '"'))
optsdict = ast.literal_eval(str(opts))
argsdict = ast.literal_eval(str(args))

links = {}
nodes = {}

def addlink(source, target):
    if not source in links:
    	links[source] = {}
    if not source in nodes:
    	nodes[source] = {"source": 0, "target": 1}
    else:
    	nodes[source]["target"] = nodes[source]["target"] + 1
    userlink = links[source]
    if target in userlink:
    	userlink[target] = userlink[target] + 1;
    else:
    	userlink[target] = 1;
    if target in nodes:
    	nodes[target]["source"] = nodes[target]["source"] + 1
    else:
    	nodes[target] = {"source": 1, "target": 0}



# nodes will end up as ["userA", "userB", ...]
# links will end up as 
#	{
#		"userA": {"userB": 3, ...},
#		"userB": {"userA": 1, ...},
#		...
#	}
#	
# Meaning that userA mentions userB 3 times, and userB mentions userA once.


for line in fileinput.input(args):
    try:
		tweet = json.loads(line)
		user = tweet["user"]["screen_name"]
		if opts.mode == 'mentions':
			if "user_mentions" in tweet["entities"]:
				for mention in tweet["entities"]["user_mentions"]:
					addlink(user, str(mention["screen_name"]))
		elif opts.mode == 'replies':
			if not(tweet["in_reply_to_screen_name"] == None):
				addlink(tweet["in_reply_to_screen_name"], user)
		else: # default mode: retweets
			if "retweeted_status" in tweet:
				addlink(user, tweet["retweeted_status"]["user"]["screen_name"])
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)

json = d3json.nodeslinktrees(nodes, links, optsdict, argsdict)

if opts.output == "json":
	print json
else:
	d3json.embed(opts.template, json)
