#!/usr/bin/env python

"""
Run this where you have a bunch of twarc JSON files and it will 
print out the start, end ranges for them.
"""

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

for filename in sys.argv[1:]:
    if filename.endswith('.json'):
        # note: tweets are in reverse chronological order
        # so the first tweet is the latest ...
        first, last, count = first_last(filename)
        print
        print filename 
        print "  start: %s [%s]" % (last["id_str"], last["created_at"])
        print "  end:   %s [%s]" % (first["id_str"], first["created_at"])
        print "  total: %s" % count
