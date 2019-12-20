#!/usr/bin/env python3

#
# This program will read tweet ids (Snowflake IDs) from a file or a pipe and 
# write the tweet ids back out again with their extracted creation time 
# (RFC 3339) as csv.
#
# usage: flakey.py ids.txt > ids-times.csv
#
# For more about Snowflake IDs see:
# https://ws-dl.blogspot.com/2019/08/2019-08-03-tweetedat-finding-tweet.html
#

import fileinput
from datetime import datetime

def id2time(tweet_id):
    ms = (tweet_id >> 22) + 1288834974657
    dt = datetime.utcfromtimestamp(ms // 1000)
    return dt.replace(microsecond=ms % 1000 * 1000)

print('id,created_at')
for line in fileinput.input():
    tweet_id = int(line) 
    created_at = id2time(tweet_id).strftime('%Y-%m-%dT%H:%M:%S.%f')[0:-3] + 'Z'
    print("{},{}".format(tweet_id, created_at))
