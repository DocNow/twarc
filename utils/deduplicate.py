#!/usr/bin/env python
"""
Given a JSON file, remove any tweets with duplicate IDs.

(`twarc.py --scrape` may result in duplicate tweets.)

Optionally, this will extract retweets. (That is, for a retweet
use tweet from retweeted_status and retweet.)

Example usage:
utils/deduplicate.py tweets.jsonl > tweets_deduped.jsonl
"""

from __future__ import print_function
import json
import fileinput
import argparse


def main(files, extract_retweets=False):
    seen = {}
    for line in fileinput.input(files=files):
        tweet = json.loads(line)
        if extract_retweets and 'retweeted_status' in tweet:
            tweet = tweet['retweeted_status']
        id = tweet["id"]
        if id not in seen:
            seen[id] = True
            print(json.dumps(tweet))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract-retweets', action='store_true', help='Extract retweets')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    main(args.files if len(args.files) > 0 else ('-',), extract_retweets=args.extract_retweets)

