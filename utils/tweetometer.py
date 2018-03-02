#!/usr/bin/env python3

"""
Reads tweet or Twitter user JSON and outputs a CSV of when the user account was
created, how many tweets they have sent to date, and their average tweets per
hour. The unit of measurement can be changed to second, minute, day and year
with the --unit option.
"""

import json
import optparse
import fileinput
import dateutil.parser
from datetime import datetime, timezone


op = optparse.OptionParser()
op.add_option('--unit', choices=['second', 'minute', 'hour', 'day', 'year'], default='hour')

opts, args = op.parse_args()

if opts.unit == 'second':
    div = 1
elif opts.unit == 'minute':
    div = 60
elif opts.unit == 'hour':
    div = 60 * 60
elif opts.unit == 'day':
    div = 60 * 60 * 24
elif opts.unit == 'year':
    div = 60 * 60 * 24 * 365

now = datetime.now(timezone.utc)

print('scree_name,tweets per %s' % opts.unit)

for line in fileinput.input(args):
    t = json.loads(line)
    if 'user' in t:
        u = t['user']
    elif 'screen_name' in t:
        u = t
    else:
        raise Exception("not a tweet or user JSON object")

    created_at = dateutil.parser.parse(u['created_at'])
    age = now - created_at
    unit = age.total_seconds() / float(div)
    total = u['statuses_count']
    tweets_per_unit = total / unit
    print('%s,%s,%s,%0.2f' % (
        u['screen_name'], 
        total,
        created_at,
        tweets_per_unit
    ))
