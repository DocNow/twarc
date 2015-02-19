#!/usr/bin/env python

"""
Pass in paths to twarc JSON files and get out summary information about them
including start/end times & ids.
"""
from __future__ import print_function

import sys
import json

def first_last(filename):
    first = last = None
    count = 0
    for line in open(filename):
        count += 1
        if not first:
            first = json.loads(line)
    last = json.loads(line)
    return first, last, count

files = []
for filename in sys.argv[1:]:
    if filename.endswith('.json'):
        # note: tweets are in reverse chronological order
        # so the first tweet is the latest ...
        first, last, count = first_last(filename)
        files.append({
            "filename": filename,
            "first": first,
            "last": last,
            "count": count
        })

files.sort(lambda a, b: cmp(a['first']['id_str'], b['first']['id_str']))
for f in files:
    print()
    print(f['filename'])
    print("  start: %s [%s]" % (f['last']["id_str"], f['last']["created_at"]))
    print("  end:   %s [%s]" % (f['first']["id_str"], f['first']["created_at"]))
    print("  total: %s" % f['count'])
