#!/usr/bin/env python

# build a reply, quote, retweet network from a file of tweets and write it 
# out as a gexf, dot, json or  html file. You will need to have networkx 
# installed and pydotplus if you want to use dot. The html presentation 
# uses d3 to display the network graph in your browser.
# 
#   ./network.py tweets.json network.html
#
# or 
#   ./network.py tweets.json network.dot
#
# or
# 
#  ./network.py tweets.json network.gexf
# 
# TODO: this is mostly here some someone can improve it :)

import sys
import json
import networkx
import optparse

from networkx import nx_pydot
from networkx.readwrite import json_graph

usage = "network.py tweets.json graph.html"
opt_parser = optparse.OptionParser(usage=usage)
opt_parser.add_option("--retweets", dest="retweets", action="store_true")
options, args = opt_parser.parse_args()

if len(args) != 2:
    opt_parser.error("must supply input and output file names")

tweets, output = args

G = networkx.DiGraph()

for line in open(tweets):
    try:
        t = json.loads(line)
    except:
        continue
    from_id = t['id_str'] 
    from_user = t['user']['screen_name']
    to_user = None
    to_id = None
    type = None

    if 'in_reply_to_status_id_str' in t:
        to_id = t['in_reply_to_status_id_str']
        type = "reply"
    if 'quoted_status' in t:
        to_id = t['quoted_status']['id_str']
        to_user = t['quoted_status']['user']['screen_name']
        type = "quote"
    if options.retweets and 'retweeted_status' in t:
        to_id = t['retweeted_status']['id_str']
        to_user = t['retweeted_status']['user']['screen_name']
        type = "retweet"

    if to_id:
        G.add_node(from_id, screen_name=from_user, type=type)
        if to_user:
            G.add_node(to_id, screen_name=to_user)
        else:
            G.add_node(to_id)
        G.add_edge(from_id, to_id, type=type)

def to_json(g):
    j = {"nodes": [], "links": []}
    for node_id, node_attrs in g.nodes(True):
        j["nodes"].append({
            "id": node_id,
            "type": node_attrs.get("type"),
            "screen_name": node_attrs.get("screen_name")
        })
    for source, target, attrs in g.edges(data=True):
        j["links"].append({
            "source": source,
            "target": target,
            "type": attrs.get("type")
        })
    return j

if output.endswith(".gexf"):
    networkx.write_gexf(G, output)

elif output.endswith(".dot"):
    nx_pydot.write_dot(G, output)

elif output.endswith(".json"):
    json.dump(to_json(G), open(output, "w"), indent=2)

elif output.endswith(".html"):
    graph_data = json.dumps(to_json(G), indent=2)
    html = """<!DOCTYPE html>
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
""" % graph_data
    open(output, "w").write(html)
