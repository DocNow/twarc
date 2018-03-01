#!/usr/bin/env python3

import json
import fileinput
import dateutil.parser
from datetime import datetime, timezone

now = datetime.now(timezone.utc)

for line in fileinput.input():
    u = json.loads(line)
    created_at = dateutil.parser.parse(u['created_at'])
    age = now - created_at
    days = age.total_seconds() / 60.0 / 60.0 / 24.0
    total = u['statuses_count']
    tweets_per_day = total / days
    print('%s,%s,%s,%0.2f' % (
        u['screen_name'], 
        total,
        created_at,
        tweets_per_day
    ))
