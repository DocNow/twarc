#!/usr/bin/env python

import os
import sys
import json

def nodeslinks(threshold):

	nodes = []
	links = []
	
	# lines look like "nodeA,nodeB,123"
	for line in sys.stdin:
		tokens = line.split(",")
		# use try to ignore header line
		try:
			if int(tokens[2]) >= threshold:
				if not tokens[0] in nodes:
					nodes.append(tokens[0])
				if not tokens[1] in nodes:
					nodes.append(tokens[1])
				links.append({"source": nodes.index(tokens[0]), 
				"target": nodes.index(tokens[1]), 
				"value": int(tokens[2])}) 
		except:
			continue
	
	nodelist = []
	for node in nodes:
		nodelist.append({"name": node})
	
	print json.dump({"nodes": nodelist, "links": links})

def nodeslinktrees(nodes, links, opts, args):
	# generate nodes json
	nodesoutput = []
	usernames = []
	for u in nodes.iterkeys():
		node = nodes[u]
		usernames.append(u)
		nodesoutput.append({"name": u, 
			"title": str(u + " (" + str(node["source"]) + "/" + str(node["target"]) + ")")})
	   
	# generate links json
	linksoutput = []
	for source in links.iterkeys():
		for target in links[source].iterkeys():
			value = links[source][target]
			if value >= opts["threshold"]:
				linksoutput.append({"source": usernames.index(target), 
					"target": usernames.index(source), 
					"value": value})

	return {"nodes": nodesoutput, "links": linksoutput, "opts": opts, "args": args}

def embed(template, d3json):
	# generate html by replacing token
	template_file = os.path.join(os.path.dirname(__file__), "templates", template)
	with open (template_file, "r") as template:
		print template.read().replace('$JSON$', json.dumps(d3json))
