#!/usr/bin/env python

# read tweets and write out a gexf file for loading into Gephi. You'll
# need to have networkx installed.
# 
#     ./gexf.py tweets.json > tweets.gexf 
# 
# TODO: this is mostly here some someone can improve it :)

import json
import fileinput

from networkx import DiGraph
from networkx.readwrite.gexf import generate_gexf

G = DiGraph()

for line in fileinput.input():
    tweet = json.loads(line)
    from_id = tweet['id_str']
    to_id = tweet.get('in_reply_to_status_id_str')

    if to_id:
        G.add_node(from_id, user=tweet['user']['screen_name'])
        G.add_node(to_id)
        G.add_edge(from_id, to_id)

for line in generate_gexf(G):
    print(line)

