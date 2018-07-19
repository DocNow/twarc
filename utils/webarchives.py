#!/usr/bin/env python3

"""
A program to filter tweets that contain links to a web archive. At the moment it
supports archive.org and archive.is, but please add more if you want!
"""

import json
import fileinput

archives = [
    'archive.is',
    'web.archive.org',
    'wayback.archive.org'
]

for line in fileinput.input():
    tweet = json.loads(line)
    for url in tweet['entities']['urls']:
        for host in archives:
            if host in url['expanded_url']:
                print(line, end='')
                done = True
        # prevent outputting same data twice if it contains
        # multiple archive urls
        if done:
            break
