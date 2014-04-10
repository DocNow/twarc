#!/usr/bin/env python

"""
Print out the URLs in a tweet json stream.
"""

import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)
    for url in tweet["entities"]["urls"]:
        if 'unshortened_url' in url:
            print url['unshortened_url']
        elif "expanded_url" in url_dict:
            print url['expanded_url']
        else:
            print url['url']
