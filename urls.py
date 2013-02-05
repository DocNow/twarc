#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    for url in tweet["entities"]["urls"]:
        if url["expanded_url"]:
            print url["expanded_url"]
        else:
            print url
