#!/usr/bin/env python3

"""
This utility Will read in user ids, or tweet JSON data, and look up each
user_id. If the user no longer exists the user_id or tweet JSON will be written
to stdout. If the user exists no output will be written. It acts like a filter
to locate deleted accounts.
"""

import re
import json
import twarc
import logging
import fileinput

logging.basicConfig(filename="deleted_users.log", level=logging.INFO)
t = twarc.Twarc()

for line in fileinput.input():
    line = line.strip()

    if re.match("^\d+$", line):
        user_id = line
    else:
        tweet = json.loads(line)
        user_id = tweet["user"]["id_str"]
    try:
        user = next(t.user_lookup([user_id]))
    except Exception as e:
        print(line)
