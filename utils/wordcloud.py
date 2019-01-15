#!/usr/bin/env python

from __future__ import print_function
import re
import sys
import json
import fileinput

def main():
	try:
		from urllib import urlopen  # Python 2
	except ImportError:
		from urllib.request import urlopen  # Python 3

	MAX_WORDS = 100

	word_counts = {}
	stop_words = set(["a","able","about","across","actually","after","against","agreed","all","almost","already","also","am","among","an","and","any","anyone","anyway","are","as","at","be","because","been","being","between","but","by","can","cannot","come","could","dear","did","do","does","either","else","ever","every","for","from","get","getting","got","had","has","have","he","her","here","hers","hey","hi","him","his","how","however","i","i'd","i'll","i'm","if","in","into","is","isnt","isn't","it","its","just","kind","last","latest","least","let","like","likely","look","make","may","me","might","more","most","must","my","neither","new","no","nor","not","now","of","off","often","on","only","or","other","our","out","over","own","part","piece","play","put","putting","rather","real","really","said","say","says","she","should","simply","since","so","some","than","thanks","that","that's","thats","the","their","them","then","there","these","they","they're","this","those","tis","to","too","try","twas","us","use","used","uses","via","wants","was","way","we","well","were","what","when","where","which","while","who","whom","why","will","with","would","yet","you","your","you're","youre"])

	for line in fileinput.input():
		try:
			tweet = json.loads(line)
		except:
			pass
		for word in text(tweet).split(' '):
			word = word.lower()
			word = word.replace(".", "")
			word = word.replace(",", "")
			word = word.replace("...", "")
			word = word.replace("'", "")
			word = word.replace(":", "")
			word = word.replace("(", "")
			word = word.replace(")", "")
			if len(word) < 3: continue
			if len(word) > 15: continue
			if word in stop_words: continue
			if word[0] in ["@", "#"]: continue
			if re.match('https?', word): continue
			if word.startswith("rt"): continue
			if not re.match('^[a-z]', word, re.IGNORECASE): continue
			word_counts[word] = word_counts.get(word, 0) + 1

	sorted_words = list(word_counts.keys())
	sorted_words.sort(key = lambda x: word_counts[x], reverse=True)
	top_words = sorted_words[0:MAX_WORDS]

	words = []
	count_range = word_counts[top_words[0]] - word_counts[top_words[-1]] + 1
	size_ratio = 100.0 / count_range
	for word in top_words:
		size = int(word_counts[word] * size_ratio) + 15
		words.append({
			"text": word,
			"size": size
		})

	wordcloud_js = urlopen('https://raw.githubusercontent.com/jasondavies/d3-cloud/master/build/d3.layout.cloud.js').read()

	output = """<!DOCTYPE html>
	<html>
	<head>
	<meta charset="utf-8">
	<title>twarc wordcloud</title>
	<script src="http://d3js.org/d3.v3.min.js"></script>
	</head>
	<body>
	<script>

	  // embed Jason Davies' d3-cloud since it's not available in a CDN
	  %s

	  var fill = d3.scale.category20();
	  var words = %s

	  d3.layout.cloud().size([800, 800])
		  .words(words)
		  .rotate(function() { return ~~(Math.random() * 2) * 90; })
		  .font("Impact")
		  .fontSize(function(d) { return d.size; })
		  .on("end", draw)
		  .start();

	  function draw(words) {
		d3.select("body").append("svg")
			.attr("width", 1000)
			.attr("height", 1000)
		  .append("g")
			.attr("transform", "translate(400,400)")
		  .selectAll("text")
			.data(words)
		  .enter().append("text")
			.style("font-size", function(d) { return d.size + "px"; })
			.style("font-family", "Impact")
			.style("fill", function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("transform", function(d) {
			  return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
			})
			.text(function(d) { return d.text; });
	  }
	</script>
	</body>
	</html>
	""" % (wordcloud_js.decode('utf8'), json.dumps(words, indent=2))

	sys.stdout.write(output)

def text(t):
    if 'full_text' in t:
        return t['full_text']
    return t['text']

if __name__ == "__main__":
    main()
