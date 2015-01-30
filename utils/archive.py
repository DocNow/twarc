#!/usr/bin/env python

"""
This little utility uses twarc to write Twitter search results to a directory
of your choosing. It will use the previous results to determine when to stop
searching.

So for example if you want to search for tweets mentioning "ferguson" you can 
run it:

    ./archive.py ferguson /mnt/tweets/ferguson

The first time you run this it will search twitter for tweets matching 
"ferguson" and write them to a file:

    /mnt/tweets/ferguson/tweets-0001.json

When you run the exact same command again:

    ./archive.py ferguson /mnt/tweets/ferguson

it will get the first tweet id in tweets-0001.json and use it to write another 
file which includes any new tweets since that tweet:

    /mnt/tweets/ferguson/tweets-0002.json

This functionality was initially part of twarc.py itself (not in a utility).
If it proves useful perhaps it can go back in. But for now twarc.py writes
to stdout to let you manage your data the way you want to.

"""

import os
import re
import json
import twarc
import logging
import argparse

archive_file_fmt = "tweets-%04i.json"
archive_file_pat = "tweets-(\d{4}).json$"

def main():
    parser = argparse.ArgumentParser("search_archive")
    parser.add_argument("search", action="store",
                        help="search for tweets matching a query")
    parser.add_argument("archive_dir", action="store",
                        help="a directory where results are stored")
    args = parser.parse_args()

    if not os.path.isdir(args.archive_dir):
        os.mkdir(args.archive_dir)

    logging.basicConfig(
        filename=os.path.join(args.archive_dir, "search_archive.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    logging.info("logging search for %s to %s", args.search, args.archive_dir)

    t = twarc.Twarc()
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


