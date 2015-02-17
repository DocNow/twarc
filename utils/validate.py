#!/usr/bin/env python

import sys
import json
import fileinput

line_number = 0

for line in fileinput.input():
    line_number += 1
    try:
        tweet = json.loads(line)
    except Exception as e:
        sys.stderr.write("invalid JSON (%s) line %s: %s" % (e, line_number, line))
