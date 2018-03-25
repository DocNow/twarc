#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput

for line in fileinput.input():
    tweet = json.loads(line)
    print(("%s [%s]" % (tweet["user"]["name"], tweet["user"]["screen_name"])))
