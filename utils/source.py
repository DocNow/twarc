#!/usr/bin/env python
"""
Util to count which clients are most used.

Example usage:
utils/source.py tweets.jsonl > sources.html
"""
import json
import fileinput
from collections import defaultdict

summary = defaultdict(int)
for line in fileinput.input():
    tweet = json.loads(line)

    source = tweet["source"]
    summary[source] += 1

sumsort = sorted(summary, key=summary.get, reverse=True)

print(
    """<!doctype html>
<html>

<head>
  <meta charset="utf-8">
  <title>Twitter client sources</title>
  <style>
    body {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 12pt;
      margin-left: auto;
      margin-right: auto;
      width: 95%;
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
  <h1>Twitter client sources</h1>
  <em>created on the command line with <a href="https://github.com/DocNow/twarc">twarc</a></em>
  </header>

  <table>
"""
)

for source in sumsort:
    print("<tr><td>{}</td><td>{}</td></tr>".format(source, summary[source]))
print(
    """


</table>

<footer id="page">
<hr>
<br>
created on the command line with <a href="https://github.com/DocNow/twarc">twarc</a>.
<br>
<br>
</footer>

</body>
</html>"""
)

# End of file
