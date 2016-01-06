#!/usr/bin/env python

"""
This little utility uses twarc to write Twitter search results to a directory
of your choosing. It will use the previous results to determine when to stop
searching.

So for example if you want to search for tweets mentioning "ferguson" you can 
run it:

    % twarc-archive.py ferguson /mnt/tweets/ferguson

The first time you run this it will search twitter for tweets matching 
"ferguson" and write them to a file:

    /mnt/tweets/ferguson/tweets-0001.json

When you run the exact same command again:

    % twarc-archive.py ferguson /mnt/tweets/ferguson

it will get the first tweet id in tweets-0001.json and use it to write another 
file which includes any new tweets since that tweet:

    /mnt/tweets/ferguson/tweets-0002.json

This functionality was initially part of twarc.py itself, but has been split out
into a separate utility.

"""
from __future__ import print_function

import os
import re
import sys
import json
import twarc
import logging
import argparse

archive_file_fmt = "tweets-%04i.json"
archive_file_pat = "tweets-(\d{4}).json$"

def main():
    e = os.environ.get
    parser = argparse.ArgumentParser("archive")
    parser.add_argument("search", action="store",
                        help="search for tweets matching a query")
    parser.add_argument("archive_dir", action="store",
                        help="a directory where results are stored")
    parser.add_argument("--consumer_key", action="store",
                        default=e('CONSUMER_KEY'),
                        help="Twitter API consumer key")
    parser.add_argument("--consumer_secret", action="store",
                        default=e('CONSUMER_SECRET'),
                        help="Twitter API consumer secret")
    parser.add_argument("--access_token", action="store",
                        default=e('ACCESS_TOKEN'),
                        help="Twitter API access key")
    parser.add_argument("--access_token_secret", action="store",
                        default=e('ACCESS_TOKEN_SECRET'),
                        help="Twitter API access token secret")
    parser.add_argument("--profile", action="store", default="main")
    parser.add_argument('-c', '--config',
                        default=twarc.default_config_filename(),
                        help="Config file containing Twitter keys and secrets")
    args = parser.parse_args()

    if not os.path.isdir(args.archive_dir):
        os.mkdir(args.archive_dir)

    logging.basicConfig(
        filename=os.path.join(args.archive_dir, "archive.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    if not (args.consumer_key and args.consumer_secret and args.access_token and args.access_token_secret):
        credentials = twarc.load_config(args.config, args.profile)
        if credentials:
            args.consumer_key = credentials['consumer_key']
            args.consumer_secret = credentials['consumer_secret']
            args.access_token = credentials['access_token']
            args.access_token_secret = credentials['access_token_secret']
        else:
            print(argparse.ArgumentTypeError("Please make sure to use command line arguments to set the Twitter API keys or set the CONSUMER_KEY, CONSUMER_SECRET ACCESS_TOKEN and ACCESS_TOKEN_SECRET environment variables"))
            sys.exit(1)

    logging.info("logging search for %s to %s", args.search, args.archive_dir)

    t = twarc.Twarc(args.consumer_key, args.consumer_secret, args.access_token,
            args.access_token_secret)

    last_archive = get_last_archive(args.archive_dir)
    if last_archive:
        last_id = json.loads(next(open(last_archive)))['id_str']
        tweets = t.search(args.search, since_id=last_id)
    else:
        tweets = t.search(args.search)

    next_archive = get_next_archive(args.archive_dir)

    # we only create the file if there are new tweets to save 
    # this prevents empty archive files
    fh = None 

    for tweet in tweets:
        if not fh:
            fh = open(next_archive, "w")
        logging.info("archived %s", tweet["id_str"])
        fh.write(json.dumps(tweet))
        fh.write("\n")

    if fh:
        fh.close()
    else: 
        logging.info("no new tweets found for %s", args.search)

def get_last_archive(archive_dir):
    count = 0
    for filename in os.listdir(archive_dir):
        m = re.match(archive_file_pat, filename)
        if m and int(m.group(1)) > count:
            count = int(m.group(1))
    if count != 0:
        return os.path.join(archive_dir, archive_file_fmt % count)
    else:
        return None

def get_next_archive(archive_dir):
    last_archive = get_last_archive(archive_dir)
    if last_archive:
        m = re.search(archive_file_pat, last_archive)
        count = int(m.group(1)) + 1
    else:
        count = 1
    return os.path.join(archive_dir, archive_file_fmt % count)


if __name__ == "__main__":
    main()


