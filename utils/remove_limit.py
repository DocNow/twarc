#!/usr/bin/env python

"""
Utility to remove limit warnings from Filter API output.

If --warnings was used, you will have the following in output:
{"limit": {"track": 2530, "timestamp_ms": "1482168932301"}}

This utility removes any limit warnings from output.

Usage:
    remove_limit.py aleppo.jsonl > aleppo_no_warnings.jsonl
"""

from __future__ import print_function
import sys
import json
import fileinput

limitbreaker = '{"limit":{"track":'
limit_breaker = '{"limit": {"track":'

for line in fileinput.input():
    if limitbreaker not in line and limit_breaker not in line:
        print(json.dumps(line))
