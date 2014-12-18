#!/usr/bin/env python

import sys
import json
import optparse
import fileinput
import dateutil.parser

opt_parser = optparse.OptionParser()
opt_parser.add_option("-f", "--format", dest="format", 
    default='%Y-%m-%d %H:%M:%S')
opts, args = opt_parser.parse_args()

for line in fileinput.input(args):
    try:
        tweet = json.loads(line)
        created_at = dateutil.parser.parse(tweet["created_at"])
        print created_at.strftime(opts.format)
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)


