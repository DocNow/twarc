#!/usr/bin/env python

"""
Prints out the tweet ids and counts of most retweeted.
"""
from __future__ import print_function

import json
import optparse
import fileinput

from collections import defaultdict

def main():
    parser = optparse.OptionParser()
    options, argv = parser.parse_args()

    counts = defaultdict(int)
    for line in fileinput.input(argv):
        try:
            tweet = json.loads(line)
        except:
            continue
        if 'retweeted_status' not in tweet:
            continue

        rt = tweet['retweeted_status']
        id = rt['id_str']
        count = rt['retweet_count']
        if count > counts[id]:
            counts[id] = count

    for id in sorted(counts, key=counts.get, reverse=True):
        print("{},{}".format(id, counts[id]))

if __name__ == "__main__":
    main()
