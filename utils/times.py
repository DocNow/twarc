#!/usr/bin/env python
from __future__ import print_function

import sys
import json
import optparse
import fileinput
import dateutil.parser

from dateutil import tz

to_zone = tz.tzlocal()

opt_parser = optparse.OptionParser()
opt_parser.add_option("-f", "--format", dest="format",
    default='%Y-%m-%d %H:%M:%S')
opt_parser.add_option('-l', "--local", dest="local", action="store_true")
opts, args = opt_parser.parse_args()

for line in fileinput.input(args):
    try:
        tweet = json.loads(line)
        created_at = dateutil.parser.parse(tweet["created_at"])
        # convert to local time
        if opts.local:
            created_at = created_at.astimezone(to_zone)
        print(created_at.strftime(opts.format))
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)
