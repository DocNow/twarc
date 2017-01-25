#!/usr/bin/env python

# build a reply, quote, retweet network from a file of tweets and write it 
# out as a gexf or dot file. You will need to have networkx installed
# and pydotplus if you want to use dot.
# 
#     ./network.py tweets.json network.gexf
# 
# TODO: this is mostly here some someone can improve it :)

import sys
import json
import networkx

from networkx import nx_pydot

if len(sys.argv) != 3:
    sys.exit("usage: network.py tweets.json network.dot")

tweets = sys.argv[1]
output = sys.argv[2]

G = networkx.DiGraph()

for line in open(tweets):
    t = json.loads(line)
    from_id = t['id_str'] 
    to_id = None
    edge_type = None

    if 'in_reply_to_status_id_str' in t:
        to_id = t['in_reply_to_status_id_str']
        edge_type = "reply"
    if 'quoted_status' in t:
        to_id = t['quoted_status']['id_str']
        edge_type = "quote"
    if 'retweeted_status' in t:
        to_id = t['retweeted_status']['id_str']
        edge_type = "retweet"

    if to_id:
        G.add_node(from_id, user=t['user']['screen_name'])
        G.add_node(to_id)
        G.add_edge(from_id, to_id, type=edge_type)

if output.endswith(".gexf"):
    networkx.write_gexf(G, output)
elif output.endswith(".dot"):
    nx_pydot.write_dot(G, output)


