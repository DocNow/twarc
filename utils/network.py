#!/usr/bin/env python

# NOTE:
#
# This script has been ported to the twarc-network plugin for working
# with data collected with twarc2. Please see
# https://github.com/docnow/twarc-newtwork for details.
#
# ---
#
# build a reply, quote, retweet network from a file of tweets and write it
# out as a gexf, dot, json or  html file. You will need to have networkx
# installed and pydotplus if you want to use dot. The html presentation
# uses d3 to display the network graph in your browser.
#
#   ./network.py tweets.jsonl network.html
#
# or
#   ./network.py tweets.jsonl network.dot
#
# or
#
#  ./network.py tweets.jsonl network.gexf
#
# if you would rather have the network oriented around nodes that are users
# instead of tweets use the --users flag
#
#  ./network.py --users tweets.jsonl network.gexf
#
# if you would rather have the network oriented around nodes that are hashtags
# instead of tweets or users, use the --hashtags flag
#
# TODO: this is mostly here some someone can improve it :)

import sys
import json
import networkx
import optparse
import itertools
import time

from networkx import nx_pydot
from networkx.readwrite import json_graph

usage = "network.py tweets.jsonl graph.html"
opt_parser = optparse.OptionParser(usage=usage)

opt_parser.add_option(
    "--retweets", dest="retweets", action="store_true", help="include retweets"
)

opt_parser.add_option(
    "--min_subgraph_size",
    dest="min_subgraph_size",
    type="int",
    help="remove any subgraphs with a size smaller than this number",
)

opt_parser.add_option(
    "--max_subgraph_size",
    dest="max_subgraph_size",
    type="int",
    help="remove any subgraphs with a size larger than this number",
)

opt_parser.add_option(
    "--users",
    dest="users",
    action="store_true",
    help="show user relations instead of tweet relations",
)


opt_parser.add_option(
    "--hashtags",
    dest="hashtags",
    action="store_true",
    help="show hashtag relations instead of tweet relations",
)

options, args = opt_parser.parse_args()

if len(args) != 2:
    opt_parser.error("must supply input and output file names")

tweets, output = args

G = networkx.DiGraph()


def add(from_user, from_id, to_user, to_id, type, created_at=None):
    "adds a relation to the graph"
    # storing start_data will allow for timestamps for gephi timeline, where nodes will appear on screen at their start dataset
    # and stay on forever after

    if (options.users or options.hashtags) and to_user:
        G.add_node(from_user, screen_name=from_user, start_date=created_at)
        G.add_node(to_user, screen_name=to_user, start_date=created_at)

        if G.has_edge(from_user, to_user):
            weight = G[from_user][to_user]["weight"] + 1
        else:
            weight = 1
        G.add_edge(from_user, to_user, type=type, weight=weight)

    elif not options.users and to_id:
        G.add_node(from_id, screen_name=from_user, type=type)
        if to_user:
            G.add_node(to_id, screen_name=to_user)
        else:
            G.add_node(to_id)
        G.add_edge(from_id, to_id, type=type)


def to_json(g):
    j = {"nodes": [], "links": []}
    for node_id, node_attrs in g.nodes(True):
        j["nodes"].append(
            {
                "id": node_id,
                "type": node_attrs.get("type"),
                "screen_name": node_attrs.get("screen_name"),
            }
        )
    for source, target, attrs in g.edges(data=True):
        j["links"].append(
            {"source": source, "target": target, "type": attrs.get("type")}
        )
    return j


for line in open(tweets):
    try:
        t = json.loads(line)
    except:
        continue
    from_id = t["id_str"]
    from_user = t["user"]["screen_name"]
    from_user_id = t["user"]["id_str"]
    to_user = None
    to_id = None
    # standardize raw created at date to dd/MM/yyyy HH:mm:ss
    created_at_date = time.strftime(
        "%d/%m/%Y %H:%M:%S",
        time.strptime(t["created_at"], "%a %b %d %H:%M:%S +0000 %Y"),
    )

    if options.users:
        for u in t["entities"].get("user_mentions", []):
            add(from_user, from_id, u["screen_name"], None, "reply", created_at_date)

    elif options.hashtags:
        hashtags = t["entities"].get("hashtags", [])
        hashtag_pairs = list(
            itertools.combinations(hashtags, 2)
        )  # list of all possible hashtag pairs
        for u in hashtag_pairs:
            # source hashtag: u[0]['text']
            # target hashtag: u[1]['text']
            add(
                "#" + u[0]["text"],
                None,
                "#" + u[1]["text"],
                None,
                "hashtag",
                created_at_date,
            )

    else:
        if t.get("in_reply_to_status_id_str"):
            to_id = t["in_reply_to_status_id_str"]
            to_user = t["in_reply_to_screen_name"]
            add(from_user, from_id, to_user, to_id, "reply")

        if t.get("quoted_status"):
            to_id = t["quoted_status"]["id_str"]
            to_user = t["quoted_status"]["user"]["screen_name"]
            to_user_id = t["quoted_status"]["user"]["id_str"]
            add(from_user, from_id, to_user, to_id, "quote")

        if options.retweets and t.get("retweeted_status"):
            to_id = t["retweeted_status"]["id_str"]
            to_user = t["retweeted_status"]["user"]["screen_name"]
            to_user_id = t["retweeted_status"]["user"]["id_str"]
            add(from_user, from_id, to_user, to_id, "retweet")

if options.min_subgraph_size or options.max_subgraph_size:
    g_copy = G.copy()
    for g in networkx.connected_component_subgraphs(G):
        if options.min_subgraph_size and len(g) < options.min_subgraph_size:
            g_copy.remove_nodes_from(g.nodes())
        elif options.max_subgraph_size and len(g) > options.max_subgraph_size:
            g_copy.remove_nodes_from(g.nodes())
    G = g_copy

if output.endswith(".gexf"):
    networkx.write_gexf(G, output)

elif output.endswith(".gml"):
    networkx.write_gml(G, output)

elif output.endswith(".dot"):
    nx_pydot.write_dot(G, output)

elif output.endswith(".json"):
    json.dump(to_json(G), open(output, "w"), indent=2)

elif output.endswith(".html"):
    graph_data = json.dumps(to_json(G), indent=2)
    html = (
        """<!DOCTYPE html>
<meta charset="utf-8">
<script src="https://platform.twitter.com/widgets.js"></script>
<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<style>

.links line {
  stroke: #999;
  stroke-opacity: 0.8;
  stroke-width: 2px;
}

line.reply {
  stroke: #999;
}

line.retweet {
  stroke-dasharray: 5;
}

line.quote {
  stroke-dasharray: 5;
}

.nodes circle {
  stroke: red;
  fill: red;
  stroke-width: 1.5px;
}

circle.retweet {
  fill: white;
  stroke: #999;
}

circle.reply {
  fill: #999;
  stroke: #999;
}

circle.quote {
  fill: yellow;
  stroke: yellow;
}

#graph {
  width: 99vw;
  height: 99vh;
}

#tweet {
  position: absolute;
  left: 100px;
  top: 150px;
}

</style>
<svg id="graph"></svg>
<div id="tweet"></div>
<script>

var width = $(window).width();
var height = $(window).height();

var svg = d3.select("svg")
    .attr("height", height)
    .attr("width", width);

var color = d3.scaleOrdinal(d3.schemeCategory20c);

var simulation = d3.forceSimulation()
    .velocityDecay(0.6)
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));

var graph = %s;

var link = svg.append("g")
    .attr("class", "links")
  .selectAll("line")
  .data(graph.links)
  .enter().append("line")
    .attr("class", function(d) { return d.type; });

var node = svg.append("g")
    .attr("class", "nodes")
  .selectAll("circle")
  .data(graph.nodes)
  .enter().append("circle")
    .attr("r", 5)
    .attr("class", function(d) { return d.type; })
    .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

node.append("title")
    .text(function(d) { return d.id; });

node.on("click", function(d) {
  $("#tweet").empty();

  var rect = this.getBoundingClientRect();
  var paneHeight = d.type == "retweet" ? 50 : 200;
  var paneWidth = d.type == "retweet" ? 75 : 500;

  var left = rect.x - paneWidth / 2;
  if (rect.y > height / 2) {
    var top = rect.y - paneHeight;
  } else {
    var top = rect.y + 10;
  }

  var tweet = $("#tweet");
  tweet.css({left: left, top: top});

  if (d.type == "retweet") {
    twttr.widgets.createFollowButton(d.screen_name, tweet[0], {size: "large"});
  } else {
    twttr.widgets.createTweet(d.id, tweet[0], {conversation: "none"});
  }

  d3.event.stopPropagation();

});

svg.on("click", function(d) {
  $("#tweet").empty();
});

simulation
    .nodes(graph.nodes)
    .on("tick", ticked);

simulation.force("link")
    .links(graph.links);

function ticked() {
  link
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  node
      .attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
}

function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

</script>
"""
        % graph_data
    )
    open(output, "w").write(html)
