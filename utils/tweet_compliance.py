#!/usr/bin/env python

"""
Supports tweet compliance. See https://developer.twitter.com/en/docs/tweets/compliance/overview.
That is, providing the most recent version of a tweet or removing unavailable (deleted or protected)
tweets.

Also useful for splitting out available tweets from unavailable tweets.

Example usage: python tweet_compliance.py test.txt > test.json 2> test_delete.txt

For each tweet in a list of tweets or tweet ids provided by standard input or contained in files,
looks up the current tweet state.

If a tweet is not available and tweet ids are provided, the tweet id is
output to standard error.

If a tweet is not available and tweets are provided, the (deleted) tweet is output to standard error.

Otherwise, the current tweet (i.e., the tweet retrieved from the API) is returned to standard out.

Ordering is not guaranteed.

Requires Twitter API keys provided in ~/.twarc or environment variables. (See twarc.py.)
"""
from __future__ import print_function

import json
import fileinput
import twarc
import sys
import logging

# Send logging to file instead of STDERR.
logging.basicConfig(
        filename="tweet_compliance.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

t = twarc.Twarc()


def process_tweets(tweets):
    available_tweet_ids = set()
    # Hydrate the tweets.
    for tweet in t.hydrate(tweets.keys()):
        # Keep track of the tweet ids of the tweets that are available.
        available_tweet_ids.add(tweet['id_str'])
        # Print available tweets to STDOUT.
        print(json.dumps(tweet))

    # Find the unavailable tweets.
    for tweet_id, tweet in tweets.items():
        if tweet_id not in available_tweet_ids:
            # Print tweet or tweet id to STDERR
            if tweets[tweet_id]:
                print(json.dumps(tweets[tweet_id]), file=sys.stderr)
            else:
                print(tweet_id, file=sys.stderr)

tweets = {}
for line in (line.rstrip('\n') for line in fileinput.input()):
    # Add tweet or None to tweet map.
    tweet_id = line
    tweet = None
    if not line.isdigit():
        tweet = json.loads(line)
        tweet_id = tweet['id_str']
    tweets[tweet_id] = tweet

    # When get to 100, process the tweets.
    if len(tweets) == 100:
        process_tweets(tweets)
        tweets.clear()

# Process any remaining tweets.
if tweets:
    process_tweets(tweets)