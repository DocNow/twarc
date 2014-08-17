#!/usr/bin/env python

import json
import fileinput

num_results = 100
min_rt = 0
tweets = []

def insert(tweet):
    global tweets

    if len(tweets) == 0:
        tweets.append(tweet)
        return

    for i in range(0, len(tweets)):
        t = tweets[i]
        if tweet['retweet_count'] > t['retweet_count']:
            tweets.insert(i, tweet)

    # remove dupes
    seen = set()
    new_tweets = []
    for tweet in tweets:
        tweet_id = tweet['retweeted_status']['id_str']
        if tweet_id in seen:
            continue
        else:
            seen.add(tweet_id)
            new_tweets.append(tweet)
    tweets = new_tweets

    # trim less popular ones
    while len(tweets) > num_results:
        tweets.pop()

for line in fileinput.input():
    tweet = json.loads(line)
    if not tweet.has_key('retweeted_status'):
        continue

    rt = tweet['retweet_count']
    if rt > min_rt:
        insert(tweet)
        min_rt = tweets[-1]['retweet_count']

print json.dumps(tweets, indent=2)
