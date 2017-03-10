#!/usr/bin/env python

"""
This is a utility for getting the friend-of-a-friend network for a 
given twitter user. The network is expressed as tuples of user identifiers for
the user and their friend (who they follow).

User identifiers are used rather than the handles or screen_name, since the 
handles can change, and Twitter's API allows you to get friends as ids much 
faster.

You can of course turn the IDs back into usernames later if you want using
twarc.
"""

import re
import sys
import twarc
import logging
import argparse
import requests

logging.basicConfig(
    filename="foaf.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

parser = argparse.ArgumentParser("tweet.py")
parser.add_argument("user", action="store", help="user_id")
parser.add_argument("--level", type=int, action="store", default=2, 
        help="how far out into the social graph to follow")

args = parser.parse_args()

t = twarc.Twarc()

def friendships(user_id, level=2):
    """
    Pass in a user_id and you will be returned a generator of friendship 
    tuples (user_id, friend_id). By default it will return the friend
    of a friend network (level=2), but you can expand this by settings the 
    level parameter to either another number. But beware, it could run for a 
    while!
    """

    logging.info("getting friends for user %s", user_id)
    level -= 1
    try:
        for friend_id in t.friend_ids(user_id):
            yield (user_id, friend_id)
            if level > 0:
                yield from friendships(friend_id, level)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.error("can't get friends for protected user %s", user_id)
        else:
            raise(e)

if re.match("^\d+$", args.user):
    seed_user_id = args.user
else:
    seed_user_id = next(t.user_lookup([args.user]))['id_str']

for friendship in friendships(seed_user_id, args.level):
    print("%s,%s" % friendship)
