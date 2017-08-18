#!/usr/bin/env python3

"""
This program assumes that you are feeding it tweet JSON data for tweets
that have been deleted. It will use the metadata and the live web to 
analyze why each tweet appears to have been deleted.
"""

import json
import time
import logging
import fileinput
import collections
import urllib.request

from urllib.error import HTTPError


USER_OK                 = "USER_OK"
USER_DELETED            = "USER_DELETED"
USER_PROTECTED          = "USER_PROTECTED"
USER_SUSPENDED          = "USER_SUSPENDED"
TWEET_OK                = "TWEET_OK"
TWEET_DELETED           = "TWEET_DELETED"
RETWEET_DELETED         = "RETWEET_DELETED"
ORIGINAL_TWEET_DELETED  = "ORIGINAL_TWEET_DELETED"
ORIGINAL_USER_DELETED   = "ORIGINAL_USER_DELETED"
ORIGINAL_USER_PROTECTED = "ORIGINAL_USER_PROTECTED"
ORIGINAL_USER_SUSPENDED = "ORIGINAL_USER_SUSPENDED"


def main():
    counts = collections.Counter()
    for line in fileinput.input():
        tweet = json.loads(line)
        result = examine(tweet)
        print(tweet_url(tweet), result)
        counts[result] += 1
    for result, count in counts.most_common():
        print(result, count)


def examine(tweet):
    user_status = get_user_status(tweet)
    if user_status != USER_OK:
        return user_status
    else:
        retweet = tweet.get('retweeted_status', None)
        tweet_status = get_tweet_status(tweet)

        if tweet_status == TWEET_OK:
            return TWEET_OK
        elif retweet == None:
            return tweet_status
        else:
            rt_status = examine(retweet)
            if rt_status == USER_DELETED:
                return ORIGINAL_USER_DELETED
            elif rt_status == USER_PROTECTED:
                return ORIGINAL_USER_PROTECTED
            elif rt_status == USER_SUSPENDED:
                return ORIGINAL_USER_SUSPENDED
            elif rt_status == TWEET_DELETED:
                return ORIGINAL_TWEET_DELETED
            elif rt_status == TWEET_OK:
                return RETWEET_DELETED
            else:
                raise "Unexpected retweet status %s for %s" % (rt_status,
                    tweet['id_str'])


users = {}
def get_user_status(tweet):
    screen_name = tweet['user']['screen_name']
    if screen_name in users:
        return users[screen_name]

    url = "https://twitter.com/%s" % screen_name
    try:
        resp = get(url)
        html = resp.read().decode("utf8")

        if resp.url == "https://twitter.com/account/suspended":
            result = USER_SUSPENDED
        elif "This account's Tweets are protected." in html:
            result = USER_PROTECTED
        elif resp.code == 200:
            result = USER_OK
    except HTTPError as error:
        if error.code == 404:
            result = USER_DELETED
        else:
            raise Exception("unexpected http status %s for %s" % (error.code,
                url))

    users[screen_name] = result
    return result


tweets = {}
def get_tweet_status(tweet):
    url = tweet_url(tweet)
    if url in tweets:
        return tweets[url]

    try:
        resp = get(url)
        if "protected_redirect" in resp.url:
            return USER_PROTECTED
        elif resp.url == "https://twitter.com/account/suspended":
            return USER_SUSPENDED
        elif resp.code == 200:
            result = TWEET_OK
        else: 
            raise Exception("unexpected http status %s for %s" % (error.code,
                url))
    except HTTPError as error:
        if error.code == 404:
            return TWEET_DELETED
        else:
            raise Exception("unexpected http status %s for %s" % (error.code,
                url))
   
    tweets[url] = result
    return result


UA = "twarc-deletes (+https://github.com/DocNow/twarc/blob/master/utils/deletes.py)"

def get(url):
    time.sleep(.5)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        return urllib.request.urlopen(req)
    except HTTPError as error:
        if error.code == 503:
            logging.warn("got 503 on %s", url)
            time.sleep(10)
            return get(url)
        else:
            raise(error)


def tweet_url(tweet):
    return "https://twitter.com/%s/status/%s" % (
        tweet['user']['screen_name'], tweet['id_str'])


if __name__ == "__main__":
    main()
