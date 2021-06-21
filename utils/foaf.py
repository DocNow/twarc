#!/usr/bin/env python3

"""
This is a utility for getting the friend-of-a-friend network for a 
given twitter user. It writes a sqlite database as it collects the data
{user-id}.sqlite and once complete it exports that data to two csv files:

* {user-id}.csv - the user id links
* {user-id}-users.csv - metadata about the users keyed off their user id

"""

import re
import csv
import sys
import twarc
import logging
import sqlite3
import argparse
import requests

from dateutil.parser import parse as parse_datetime

logging.basicConfig(
    filename="foaf.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


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
        count = 0
        for friend_id in t.friend_ids(user_id):
            count += 1
            add_friendship(user_id, friend_id)
            yield (user_id, friend_id)
            if level > 0:
                if not user_in_db(friend_id):
                    yield from friendships(friend_id, level)
                else:
                    logging.info("already collected %s", friend_id)
            if count % 1000 == 0:
                db.commit()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.error("can't get friends for protected user %s", user_id)
        else:
            raise (e)


def user_ids():
    """
    Returns all the Twitter user_ids in the database.
    """
    sql = """
        SELECT DISTINCT(user_id) AS user_id FROM friends
        UNION
        SELECT DISTINCT(friend_id) AS user_id FROM friends
        """
    for result in db.execute(sql):
        yield str(result[0])


def user_in_db(user_id):
    """
    Checks to see if the user's friends have already been collected.
    """
    results = db.execute("SELECT COUNT(*) FROM friends where user_id = ?", [user_id])
    return results.fetchone()[0] > 0


def add_friendship(user_id, friend_id):
    """
    Add a friendship to the database.
    """
    db.execute(
        "INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", [user_id, friend_id]
    )


def add_user(u):
    """
    Add a user to the database.
    """
    db.execute(
        """
        INSERT INTO users (
          user_id,
          screen_name,
          name,
          description,
          location,
          created,
          statuses,
          verified
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            u["id"],
            u["screen_name"],
            u["name"],
            u["description"],
            u["location"],
            parse_datetime(u["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            u["statuses_count"],
            u["verified"],
        ],
    )


# get command line arguments
parser = argparse.ArgumentParser("tweet.py")
parser.add_argument("user", action="store", help="user_id")
parser.add_argument(
    "--level",
    type=int,
    action="store",
    default=2,
    help="how far out into the social graph to follow",
)
args = parser.parse_args()

# create twarc instance for querying Twitter
t = twarc.Twarc()

# get the seed user_id, potentially from their screen name
if re.match("^\d+$", args.user):
    seed_user_id = args.user
else:
    seed_user_id = next(t.user_lookup([args.user]))["id_str"]

# setup sqlite db for storing information as it is collected
db = sqlite3.connect(f"{seed_user_id}.sqlite3")
db.execute(
    """
    CREATE TABLE IF NOT EXISTS friends (
      user_id INT,
      friend_id INT,
      PRIMARY KEY (user_id, friend_id)
    )
    """
)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
      user_id INT,
      screen_name TEXT,
      name TEXT,
      description TEXT,
      location TEXT,
      created TEXT,
      statuses INT,
      verified TEXT,
      PRIMARY KEY (user_id)
    )
    """
)

# lookup friendship data
for friendship in friendships(seed_user_id, args.level):
    print("%s,%s" % friendship)

# lookup user metadata
for user in t.user_lookup(user_ids()):
    add_user(user)

db.commit()

# write out friendships
with open("{}.csv".format(seed_user_id), "w") as fh:
    w = csv.writer(fh)
    w.writerow(["user_id", "friend_user_id"])
    for row in db.execute("SELECT * FROM friends"):
        w.writerow(row)

# write out user data as csv
with open("{}-users.csv".format(seed_user_id), "w") as fh:
    w = csv.writer(fh)
    w.writerow(
        [
            "user_id",
            "screen_name",
            "name",
            "description",
            "location",
            "created",
            "statuses",
            "verified",
        ]
    )

    sql = """
        SELECT user_id, screen_name, name, description,
               location, created, statuses, verified
        FROM users
        """

    for row in db.execute(sql):
        w.writerow(row)
