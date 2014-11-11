#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feed wall.py your JSON and get a wall of tweets as HTML. If you want to get the
wall in chronological order, a handy trick is:

    % tail -r tweets.json | ./wall.py > wall.html

"""

import re
import sys
import json
import fileinput
import dateutil.parser

print """<!doctype html>
<html>

<head>
  <meta charset="utf-8">
  <title>twarc wall</title>
  <style>
    body {
      font-size: 12pt;
      margin-left: auto;
      margin-right: auto;
      width: 95%;
    }

    article.tweet {
      position: relative;
      float: left;
      border: thin #eeeeee solid;
      margin: 10px;
      width: 270px;
      padding: 10px;
      height: 170px;
    }

    .name {
      font-weight: bold;
    }

    img.avatar {
        vertical-align: middle;
        float: left;
        margin-right: 10px;
        border-radius: 5px;
        height: 45px;
    }

    .tweet footer {
      position: absolute;
      bottom: 5px;
      left: 10px;
      font-size: smaller;
    }

    .tweet a {
      text-decoration: none;
    }

    footer#page {
      margin-top: 15px;
      clear: both;
      width: 100%;
      text-align: center;
      font-size: 20pt;
      font-weight: heavy;
    }

    header {
      text-align: center;
      margin-bottom: 20px;
    }

  </style>
</head>

<body>

  <header>
  <h1>Title Here</h1>
  <em>created on the command line with <a href="http://github.com/edsu/twarc">twarc</a></em>
  </header>

  <div id="tweets">
"""

# Parse command-line args
reverse = False
# If args include --reverse, remove first it,
# leaving file name(s) (if any) in args
if len(sys.argv) > 1:
    if sys.argv[1] == "--reverse" or sys.argv[1] == "-r":
        reverse = True
        del sys.argv[0]

lines = fileinput.input()
if reverse:
    buffered_lines = []
    for line in lines:
        buffered_lines.append(line)
    # Reverse list using slice
    lines = buffered_lines[::-1]

for line in lines:
    tweet = json.loads(line)

    t = {
        "created_at": tweet["created_at"],
        "name": tweet["user"]["name"],
        "username": tweet["user"]["screen_name"],
        "user_url": "http://twitter.com/" + tweet["user"]["screen_name"],
        "text": tweet["text"],
        "avatar": tweet["user"]["profile_image_url"],
        "url": "http://twitter.com/" + tweet["user"]["screen_name"] + "/status/" + tweet["id_str"],
    }

    if 'retweet_status' in tweet:
        t['retweet_count'] = tweet['retweet_status'].get('retweet_count', 0)
    else:
        t['retweet_count'] = tweet.get('retweet_count', 0)

    for url in tweet['entities']['urls']:
        a = '<a href="%(expanded_url)s">%(url)s</a>' % url
        start, end = url['indices']
        t['text'] = t['text'][0:start] + a + tweet['text'][end:]

    t['text'] = re.sub(' @([^ ]+)', ' <a href="http://twitter.com/\g<1>">@\g<1></a>', t['text'])
    t['text'] = re.sub(' #([^ ]+)', ' <a href="https://twitter.com/search?q=%23\g<1>&src=hash">#\g<1></a>', t['text'])

    html = """
    <article class="tweet">
      <img class="avatar" src="%(avatar)s">
      <a href="%(user_url)s" class="name">%(name)s</a><br>
      <span class="username">%(username)s</span><br>
      <br>
      <span class="text">%(text)s</span><br>
      <footer>
      %(retweet_count)s Retweets<br>
      <a href="%(url)s"><time>%(created_at)s</time></a>
      </footer>
    </article>
    """ % t

    print html.encode("utf-8")

print """

</div>

<footer id="page">
<hr>
<br>
created on the command line with <a href="http://github.com/edsu/twarc">twarc</a>.
<br>
<br>
</footer>

</body>
</html>"""
