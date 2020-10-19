#!/usr/bin/env python
"""
Given a minimum and/or maximum date, filter out all tweets after this date.

For example, if a hashtag was used for another event before the one you're
interested in, you can filter out the old ones.

Example usage:
utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl
"""
from __future__ import print_function

import sys
import json
import fileinput
import argparse
import datetime
from dateutil.parser import parse


def filter_input(mindate, maxdate, files):
    mindate = parse(mindate) if mindate is not None else datetime.datetime.min
    maxdate = parse(maxdate) if maxdate is not None else datetime.datetime.max

    for line in fileinput.input(files):
        tweet = json.loads(line)

        created_at = parse(tweet["created_at"])
        created_at = created_at.replace(tzinfo=None)

        if mindate < created_at and maxdate > created_at:
            print(json.dumps(tweet))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mindate", help="the minimum date", default=None)
    parser.add_argument("--maxdate", help="the maximum date", default=None)
    parser.add_argument("files", nargs="?", default=[])
    args = parser.parse_args()

    filter_input(args.mindate, args.maxdate, args.files)


if __name__ == "__main__":
    main()
