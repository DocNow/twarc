#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feed wall.py your JSON and get a wall of tweets as HTML. If you want to get the
wall in chronological order, a handy trick is:

    % tail -r tweets.json | ./wall.py > wall.html

"""

import re
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
      height: 160px;
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
    }

    .tweet a {
      text-decoration: none;
    }

    time { 
      font-size: small;
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

# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_pattern = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')

for line in fileinput.input():
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

    t['text'] = url_pattern.sub('<a href="\g<1>">\g<1></a>', t['text'])
    t['text'] = re.sub('@([^ ]+)', '<a href="http://twitter.com/\g<1>">@\g<1></a>', t['text'])
    t['text'] = re.sub('#([^ ]+)', '<a href="https://twitter.com/search?q=%23\g<1>&src=hash">#\g<1></a>', t['text'])

    html = """
    <article class="tweet">
      <img class="avatar" src="%(avatar)s">
      <a href="%(user_url)s" class="name">%(name)s</a><br>
      <span class="username">%(username)s</span><br>
      <br>
      <span class="text">%(text)s</span><br>
      <footer>
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
