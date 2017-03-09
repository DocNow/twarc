#!/usr/bin/env python

import sys
import twarc
import logging
import argparse

logging.basicConfig(filename="foaf.log", level=logging.INFO)

parser = argparse.ArgumentParser("tweet.py")
parser.add_argument("user", action="store", help="user_id")
parser.add_argument("--level", type=int, action="store", default=1, help="how many levels of recursion to follow")

args = parser.parse_args()

t = twarc.Twarc()
t.load_config()

def friend_ids(user_id, level=1):
    level -= 1
    for friend_id in t.friend_ids(user_id):
        yield (user_id, friend_id)
        if level > 0:
            yield from friend_ids(friend_id)

for user_id, friend_id in friend_ids(args.user, args.level):
    print(user_id, friend_id)
