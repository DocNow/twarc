#!/usr/bin/env python

"""
This is a little utility that reads in tweets, rehydrates them, and only 
outputs the tweets JSON for tweets that are no longer available.
"""

import json
import twarc
import fileinput

t = twarc.Twarc()


def missing(tweets):
    tweet_ids = [t["id_str"] for t in tweets]
    hydrated = t.hydrate(tweets)
    hydrated_ids = [t["id_str"] for t in hydrated]
    missing_ids = tweet_ids - hydrated_ids
    for t in tweets:
        if t["id_str"] in missing_ids:
            yield t


tweets = []

for line in fileinput.input():
    t = json.loads(line)
    tweets.append(t)
    if len(tweets) > 100:
        for t in missing(tweets):
            print(json.dumps(t))
        tweets = []

if len(tweets) > 0:
    for t in missing(tweets):
        print(json.dumps(t))
