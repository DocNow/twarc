#!/usr/bin/env python
"""
Given a minimum date, filter out all tweets after this date.

For example, if a hashtag was used for another event before the one you're
interested in, you can filter out the old ones.

Example usage:
utils\filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl
"""
from __future__ import print_function

import sys
import json
import fileinput
import dateutil.parser


# parse command-line args
mindate = dateutil.parser.parse("1-January-2012")
# if args include --mindate, get mindate and remove first two args,
# leaving file name(s) (if any) in args
if len(sys.argv) > 1:
    if sys.argv[1] == "--mindate":
        mindate = dateutil.parser.parse(sys.argv[2])
        del sys.argv[0]
        del sys.argv[0]

# fh = open('date_filtered.jsonl', 'w')
# kept, discarded = 0, 0

for line in fileinput.input():
    tweet = json.loads(line)

    created_at = dateutil.parser.parse(tweet["created_at"])
    created_at = created_at.replace(tzinfo=None)

    # print(created_at, mindate, created_at >= mindate)
    if (created_at >= mindate):
        print(json.dumps(tweet))
        # fh.write(json.dumps(tweet))
        # fh.write("\n")
        # kept += 1
    # else:
        # discarded += 1

# print("Kept", kept, "tweets and discarded", discarded)

# End of file
