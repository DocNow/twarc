#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feed wall.py your JSON and get a wall of tweets as HTML. If you want to get the
wall in chronological order, a handy trick is:

    % tail -r tweets.jsonl | ./wall.py > wall.html

"""
from __future__ import print_function

import os
import re
import sys
import json
import requests
import fileinput

AVATAR_DIR = "img"


def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    outfile = os.path.join(AVATAR_DIR, local_filename)
    if not os.path.isfile(outfile):
        with open(outfile, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
    return local_filename

def text(t):
    return (t.get('full_text') or t.get('extended_tweet', {}).get('full_text') or t['text']).replace('\n', ' ')

print("""<!doctype html>
<html>

<head>
  <meta charset="utf-8">
  <title>twarc wall</title>
  <style>
    body {
      font-family: Arial, Helvetica, sans-serif;
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
      height: 220px;
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

    .tweet .text {
      height: 130px;
      overflow: auto;
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
""")

# Make avatar directory
if not os.path.isdir(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

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

    # Download avatar
    url = tweet["user"]["profile_image_url"]
    filename = download_file(url)

    t = {
        "created_at": tweet["created_at"],
        "name": tweet["user"]["name"],
        "username": tweet["user"]["screen_name"],
        "user_url": "http://twitter.com/" + tweet["user"]["screen_name"],
        "text": text(tweet),
        "avatar": AVATAR_DIR + "/" + filename,
        "url": "http://twitter.com/" + tweet["user"]["screen_name"] + "/status/" + tweet["id_str"],
    }

    if 'retweet_status' in tweet:
        t['retweet_count'] = tweet['retweet_status'].get('retweet_count', 0)
    else:
        t['retweet_count'] = tweet.get('retweet_count', 0)

    if t['retweet_count'] == 1:
        t['retweet_string'] = 'retweet'
    else:
        t['retweet_string'] = 'retweets'

    for url in tweet['entities']['urls']:
        a = '<a href="%(expanded_url)s">%(url)s</a>' % url
        start, end = url['indices']
        t['text'] = t['text'][0:start] + a + t['text'][end:]

    t['text'] = re.sub(' @([^ ]+)', ' <a href="http://twitter.com/\g<1>">@\g<1></a>', t['text'])
    t['text'] = re.sub(' #([^ ]+)', ' <a href="https://twitter.com/search?q=%23\g<1>&src=hash">#\g<1></a>', t['text'])

    html = u"""
    <article class="tweet">
      <img class="avatar" src="%(avatar)s">
      <a href="%(user_url)s" class="name">%(name)s</a><br>
      <span class="username">%(username)s</span><br>
      <br>
      <div class="text">%(text)s</div><br>
      <footer>
      %(retweet_count)s %(retweet_string)s<br>
      <a href="%(url)s"><time>%(created_at)s</time></a>
      </footer>
    </article>
    """ % t

    if sys.version_info.major == 2:
        print(html.encode('utf8'))
    else:
        print(html)

print("""

</div>

<footer id="page">
<hr>
<br>
created on the command line with <a href="http://github.com/edsu/twarc">twarc</a>.
<br>
<br>
</footer>

</body>
</html>""")
