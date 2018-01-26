#!/usr/bin/env python

"""
Reads a stream of twitter data and writes out data for the top 10 retweets.
Use the --results option to change the number of results.
"""
from __future__ import print_function

import json
import optparse
import fileinput

def main():
    retweets = []
    parser = optparse.OptionParser()
    parser.add_option("-r", "--results", dest="results", default=10, type="int",
                      help="number of top retweets to find")
    options, argv = parser.parse_args()

    min_rt = 0
    # TODO: maybe this index should be on disk berkeleydb or something?
    seen = set()
    for line in fileinput.input(argv):
        try:
            tweet = json.loads(line)
        except:
            continue
        if 'retweeted_status' not in tweet:
            continue
        if tweet['retweeted_status']['id_str'] in seen:
            # TODO: make this work for data that is not reverse-chrono?
            continue
        rt = tweet['retweeted_status']
        if rt['retweet_count'] > min_rt or len(retweets) < options.results:
            seen.add(rt['id_str'])
            insert(rt, retweets, options.results)
            min_rt = retweets[-1]['retweet_count']

    for rt in retweets:
        print(json.dumps(rt))

def insert(rt, retweets, num_results):
    num_retweets = len(retweets)

    if num_retweets == 0:
        retweets.append(rt)
        return

    # there's a more efficient way of doing this
    for i in range(0, len(retweets)):
        if rt['retweet_count'] > retweets[i]['retweet_count']:
            retweets.insert(i, rt)
            break

    if len(retweets) == num_retweets:
        retweets.append(rt)

    # trim less popular ones
    while len(retweets) > num_results:
        retweets.pop()

if __name__ == "__main__":
    main()
