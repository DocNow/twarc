#!/usr/bin/env python
"""
Given a JSON file, remove any tweets with duplicate IDs.

(`twarc.py --scrape` may result in duplicate tweets.)

Example usage:
utils/deduplicate.py tweets.jsonl > tweets_deduped.jsonl
"""

from __future__ import print_function
import json
import fileinput


seen = {}
for line in fileinput.input():
    tweet = json.loads(line)
    id = tweet["id"]
    if id not in seen:
        seen[id] = True
        print(json.dumps(tweet))
