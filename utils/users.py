#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    print ("%s [%s]" % (tweet["user"]["name"], tweet["user"]["screen_name"])).encode('utf-8')


