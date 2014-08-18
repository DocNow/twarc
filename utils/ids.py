#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    print tweet["id_str"]



