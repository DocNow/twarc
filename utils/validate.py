#!/usr/bin/env python

import sys
import json
import fileinput
import dateutil.parser

line_number = 0                                                                                                                                                                                        

for line in fileinput.input():
    line_number += 1 
    try:
        tweet = json.loads(line)
    except Exception as e:
        sys.stderr.write("uhoh, we got a problem on line: %d\n%s\n" % (line_number, e))
