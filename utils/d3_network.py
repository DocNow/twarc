#!/usr/bin/env python

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
# TODO: this is mostly here some someone can improve it :)

import sys
import json
import networkx
import optparse

from networkx import nx_pydot
from networkx.readwrite import json_graph

usage = "network.py tweets.jsonl graph.html"
opt_parser = optparse.OptionParser(usage=usage)

opt_parser.add_option(
    "--retweets",
    dest="retweets",
    action="store_true",
    help="include retweets"
)

opt_parser.add_option(
    "--min_subgraph_size",
    dest="min_subgraph_size",
    type="int",
    help="remove any subgraphs with a size smaller than this number"
)

opt_parser.add_option(
    "--max_subgraph_size",
    dest="max_subgraph_size",
    type="int",
    help="remove any subgraphs with a size larger than this number"
)

opt_parser.add_option(
    "--users",
    dest="users",
    action="store_true",
    help="show user relations instead of tweet relations"
)

options, args = opt_parser.parse_args()

if len(args) != 2:
    opt_parser.error("must supply input and output file names")

tweets, output = args

G = networkx.DiGraph()

def add(from_user, from_id, to_user, to_id, type):
    "adds a relation to the graph"

    if options.users and to_user:
        G.add_node(from_user, screen_name=from_user)
        G.add_node(to_user, screen_name=to_user)
       
        if G.has_edge(from_user, to_user):
            weight = G[from_user][to_user]['weight'] + 1
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

for line in open(tweets):
    try:
        t = json.loads(line)
    except:
        continue
    from_id = t['id_str']
    from_user = t['user']['screen_name']
    from_user_id = t['user']['id_str']
    to_user = None
    to_id = None

    if options.users:
        for u in t['entities'].get('user_mentions', []):
            add(from_user, from_id, u['screen_name'], None, 'reply')

    else:

        if t.get('in_reply_to_status_id_str'):
            to_id = t['in_reply_to_status_id_str']
            to_user = t['in_reply_to_screen_name']
            add(from_user, from_id, to_user, to_id, "reply")

        if t.get('quoted_status'):
            to_id = t['quoted_status']['id_str']
            to_user = t['quoted_status']['user']['screen_name']
            to_user_id = t['quoted_status']['user']['id_str']
            add(from_user, from_id, to_user, to_id, "quote")

        if options.retweets and t.get('retweeted_status'):
            to_id = t['retweeted_status']['id_str']
            to_user = t['retweeted_status']['user']['screen_name']
            to_user_id = t['retweeted_status']['user']['id_str']
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
    html = """<!DOCTYPE html>
<meta charset="utf-8">
<script src="https://platform.twitter.com/widgets.js"></script>
<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<style>

svg {
  margin: 0.5rem;
}
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
  fill: #f0027f;
  stroke: #fff;
  stroke-width: 1px;
}

circle.retweet {
  fill: white;
  stroke: #999;
}

circle.reply {
  fill: #999;
}

circle.quote {
  fill: #17becf;
}

#tweet {
  position: absolute;
}

</style>
<svg id="graph"></svg>
<div id="tweet"></div>
<script>

var width = 1750;
var height = 1750;

var radius = 3.5;

let div = d3.select('body')
        .append('div') 
        .attr('class', 'tooltip')
        .style('opacity', 0);

var svg = d3.select("svg")
    .attr("height", height)
    .attr("width", width);

svg.append("circle").attr("cx",5).attr("cy",6).attr("r", 4).style("fill", "#f0027f")
svg.append("circle").attr("cx",65).attr("cy",6).attr("r", 4).style("fill", "#17becf")
svg.append("circle").attr("cx",125).attr("cy",6).attr("r", 4).style("fill", "#999")
svg.append("text").attr("x", 15).attr("y", 7).text("Tweet").style("font-size", "14px").style("font-family", "arial, sans-serif").attr("alignment-baseline","middle")
svg.append("text").attr("x", 75).attr("y", 7).text("Quote").style("font-size", "14px").style("font-family", "arial, sans-serif").attr("alignment-baseline","middle")
svg.append("text").attr("x", 135).attr("y", 7).text("Reply").style("font-size", "14px").style("font-family", "arial, sans-serif").attr("alignment-baseline","middle")

svg.append("circle").attr("cx",183).attr("cy",6).attr("r", 4).style("fill", "#fff").style("stroke", "#999")
svg.append("text").attr("x", 193).attr("y", 7).text("Retweet").style("font-size", "14px").style("font-family", "arial, sans-serif").attr("alignment-baseline","middle")

var simulation = d3.forceSimulation()
    .velocityDecay(0.6)
    .force("link", d3.forceLink().id(d => d.id).distance(1).iterations(1))
    .force("charge", d3.forceManyBody().strength(-30).distanceMin(4).distanceMax(200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(d => 8).strength(1).iterations(1));

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
    .attr("r", radius)
    .attr("class", function(d) { return d.type; })
    .attr('cursor', 'pointer')
    .on('mouseover.fade', fade(0.1))
    .on('mouseout.fade', fade(1));

node.append("title")
    .text(function(d) { return d.screen_name; });

node.on("click", function(d) {
  $("#tweet").empty();

  var rect = this.getBoundingClientRect();
  var paneHeight = d.type == "retweet" ? 50 : 200;
  var paneWidth = d.type == "retweet" ? 75 : 500;

  var left = (d3.event.pageX + 25) + "px";
  var top = (d3.event.pageY - 28) + "px";

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

var drag_handler = d3.drag()
	.on("start", drag_start)
	.on("drag", drag_drag)
	.on("end", drag_end);	
	
drag_handler(node);

simulation
    .nodes(graph.nodes)
    .on('tick', ticked);

simulation.force('link')
    .links(graph.links);

function drag_start(d) {
 if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function drag_drag(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function drag_end(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

function ticked() {
    node
        .attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
        .attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); });
        
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
}  

const linkedByIndex = {};
  graph.links.forEach(d => {
      linkedByIndex[`${d.source.index},${d.target.index}`] = 1;
  });

  function isConnected(a, b) {
      return linkedByIndex[`${a.index},${b.index}`] || linkedByIndex[`${b.index},${a.index}`] || a.index === b.index;
  }

  function fade(opacity) {
      return d => {
        node.style('stroke-opacity', function (o) {
          const thisOpacity = isConnected(d, o) ? 1 : opacity;
          this.setAttribute('fill-opacity', thisOpacity);
          return thisOpacity;
        });
        link.style('stroke-opacity', o => (o.source === d || o.target === d ? 1 : opacity));
        link.attr('marker-end', o => (opacity === 1 || o.source === d || o.target === d ? 'url(#end-arrow)' : 'url(#end-arrow-fade)'));
      };
  }

</script>
""" % graph_data
    open(output, "w").write(html)
