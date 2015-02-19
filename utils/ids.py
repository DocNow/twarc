#!/usr/bin/env python

from __future__ import print_function
import sys
import json
import fileinput

for line in fileinput.input():
    try:
        tweet = json.loads(line)
        print(tweet["id_str"])
    except Exception as e:
        sys.stderr.write("uhoh: %s\n" % e)
