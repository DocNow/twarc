#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput
import dateutil.parser

for line in fileinput.input():
    tweet = json.loads(line)
    created_at = dateutil.parser.parse(tweet["created_at"])
    print(("[%s] @%s: %s (%s)" % (
        created_at.strftime("%Y-%m-%d %H:%M:%S"),
        tweet["user"]["screen_name"],
        tweet["text"],
        tweet["id_str"]
    )).encode('utf8'))
