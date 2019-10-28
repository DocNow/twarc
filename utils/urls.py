#!/usr/bin/env python3

"""
Print out the URLs in a tweet json stream.
"""
from __future__ import print_function

import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)
    for url in tweet["entities"]["urls"]:
        if 'unshortened_url' in url:
            print(url['unshortened_url'])
        elif url.get('expanded_url'):
            print(url['expanded_url'])
        elif url.get('url'):
            print(url['url'])
