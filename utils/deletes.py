#!/usr/bin/env python3

"""
This program assumes that you are feeding it tweet JSON data for tweets
that have been deleted. It will use the metadata and the API to
analyze why each tweet appears to have been deleted.

Note that lookups are based on user id, so may give different results than
looking up a user by screen name.
"""

import json
import fileinput
import collections
import requests
import twarc
import argparse
import logging

USER_OK = "USER_OK"
USER_DELETED = "USER_DELETED"
USER_PROTECTED = "USER_PROTECTED"
USER_SUSPENDED = "USER_SUSPENDED"
TWEET_OK = "TWEET_OK"
TWEET_DELETED = "TWEET_DELETED"
# You have been blocked by the user.
TWEET_BLOCKED = "TWEET_BLOCKED"
RETWEET_DELETED = "RETWEET_DELETED"
ORIGINAL_TWEET_DELETED = "ORIGINAL_TWEET_DELETED"
ORIGINAL_TWEET_BLOCKED = "ORIGINAL_TWEET_BLOCKED"
ORIGINAL_USER_DELETED = "ORIGINAL_USER_DELETED"
ORIGINAL_USER_PROTECTED = "ORIGINAL_USER_PROTECTED"
ORIGINAL_USER_SUSPENDED = "ORIGINAL_USER_SUSPENDED"

t = twarc.Twarc()


def main(files, enhance_tweet=False, print_results=True):
    counts = collections.Counter()
    for count, line in enumerate(fileinput.input(files=files)):
        if count % 10000 == 0:
            logging.info("processed {:,} tweets".format(count))
        tweet = json.loads(line)
        result = examine(tweet)
        if enhance_tweet:
            tweet['delete_reason'] = result
            print(json.dumps(tweet))
        else:
            print(tweet_url(tweet), result)
        counts[result] += 1
    if print_results:
        for result, count in counts.most_common():
            print(result, count)


def examine(tweet):
    user_status = get_user_status(tweet)
    # Go with user status first (suspended, protected, deleted)
    if user_status != USER_OK:
        return user_status
    else:
        retweet = tweet.get('retweeted_status', None)
        tweet_status = get_tweet_status(tweet)

        # If not a retweet and tweet deleted, then tweet deleted.

        if tweet_status == TWEET_OK:
            return TWEET_OK
        elif retweet is None or tweet_status == TWEET_BLOCKED:
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
            elif rt_status == TWEET_BLOCKED:
                return ORIGINAL_TWEET_BLOCKED
            elif rt_status == TWEET_OK:
                return RETWEET_DELETED
            else:
                raise "Unexpected retweet status %s for %s" % (rt_status,
                                                               tweet['id_str'])


users = {}


def get_user_status(tweet):
    user_id = tweet['user']['id_str']
    if user_id in users:
        return users[user_id]

    url = "https://api.twitter.com/1.1/users/show.json"
    params = {"user_id": user_id}

    # USER_DELETED: 404 and {"errors": [{"code": 50, "message": "User not found."}]}
    # USER_PROTECTED: 200 and user object with "protected": true
    # USER_SUSPENDED: 403 and {"errors":[{"code":63,"message":"User has been suspended."}]}
    result = USER_OK
    try:
        resp = t.get(url, params=params, allow_404=True)
        user = resp.json()
        if user['protected']:
            result = USER_PROTECTED
    except requests.exceptions.HTTPError as e:
        try:
            resp_json = e.response.json()
        except json.decoder.JSONDecodeError:
            raise e
        if e.response.status_code == 404 and has_error_code(resp_json, 50):
            result = USER_DELETED
        elif e.response.status_code == 403 and has_error_code(resp_json, 63):
            result = USER_SUSPENDED
        else:
            raise e

    users[user_id] = result
    return result


tweets = {}


def get_tweet_status(tweet):
    id = tweet['id_str']
    if id in tweets:
        return tweets[id]
    # USER_SUSPENDED: 403 and {"errors":[{"code":63,"message":"User has been suspended."}]}
    # USER_PROTECTED: 403 and {"errors":[{"code":179,"message":"Sorry, you are not authorized to see this status."}]}
    # TWEET_DELETED: 404 and {"errors":[{"code":144,"message":"No status found with that ID."}]}
    # or {"errors":[{"code":34,"message":"Sorry, that page does not exist."}]}

    url = "https://api.twitter.com/1.1/statuses/show.json"
    params = {"id": id}

    result = TWEET_OK
    try:
        t.get(url, params=params, allow_404=True)
    except requests.exceptions.HTTPError as e:
        try:
            resp_json = e.response.json()
        except json.decoder.JSONDecodeError:
            raise e
        if e.response.status_code == 404 and has_error_code(resp_json, (34, 144)):
            result = TWEET_DELETED
        elif e.response.status_code == 403 and has_error_code(resp_json, 63):
            result = USER_SUSPENDED
        elif e.response.status_code == 403 and has_error_code(resp_json, 179):
            result = USER_PROTECTED
        elif e.response.status_code == 401 and has_error_code(resp_json, 136):
            result = TWEET_BLOCKED
        else:
            raise e

    tweets[id] = result
    return result


def tweet_url(tweet):
    return "https://twitter.com/%s/status/%s" % (
        tweet['user']['screen_name'], tweet['id_str'])


def has_error_code(resp, code):
    if isinstance(code, int):
        code = (code, )
    for error in resp['errors']:
        if error['code'] in code:
            return True
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--enhance', action='store_true',
                        help='Enhance tweet with delete_reason and output enhanced tweet.')
    parser.add_argument('--skip-results', action='store_true', help='Skip outputting delete reason summary')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    main(args.files if len(args.files) > 0 else ('-',), enhance_tweet=args.enhance,
         print_results=not args.skip_results and not args.enhance)
