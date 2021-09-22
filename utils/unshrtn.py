#!/usr/bin/env python3

"""
Unfortunately the "expanded_url" as supplied by Twitter aren't fully
expanded one hop past t.co.

unshrtn.py will attempt to completely unshorten URLs and add them as the
"unshortened_url" key to each url, and emit the tweet as JSON again on stdout.

This script starts 10 separate processes which talk to an instance of unshrtn
that is running:

    http://github.com/edsu/unshrtn

"""

import re
import json
import time
import logging
import argparse
import fileinput
import multiprocessing
import urllib.request, urllib.parse, urllib.error

# number of urls to look up in parallel
POOL_SIZE = 10
unshrtn_url = "http://localhost:3000"
retries = 2
wait = 15

logging.basicConfig(filename="unshorten.log", level=logging.INFO)


def unshrtn_obj(obj):
    """Pass in an object and have all the object returned with additional
    unshortened_url keys
    """
    if type(obj) == list:
        return list(map(unshrtn_obj, obj))
    elif type(obj) != dict:
        return obj

    url = obj.get("expanded_url") or obj.get("url")
    if not url or re.match(r"^https?://(api.)?twitter.com/", url):
        return {k: unshrtn_obj(v) for k, v in obj.items()}

    u = "{}/?{}".format(
        unshrtn_url, urllib.parse.urlencode({"url": url.encode("utf8")})
    )
    resp = None
    for retry in range(0, retries):
        try:
            resp = json.loads(urllib.request.urlopen(u).read().decode("utf-8"))
            break
        except Exception as e:
            logging.error(
                "http error: %s when looking up %s. Try %s of %s",
                e,
                url,
                retry,
                retries,
            )
            time.sleep(wait)

    return {**obj, "unshortened_url": resp["long"]}


def rewrite_line(line):
    try:
        data = json.loads(line)
        return json.dumps(unshrtn_obj(data))
    except Exception as e:
        # garbage in, garbage out
        logging.error(e)
        return line


def main():
    global unshrtn_url, retries, wait
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pool-size",
        help="number of urls to look up in parallel",
        default=POOL_SIZE,
        type=int,
    )
    parser.add_argument(
        "--unshrtn", help="url of the unshrtn service", default=unshrtn_url
    )
    parser.add_argument(
        "--retries",
        help="number of time to retry if error from unshrtn service",
        default=retries,
        type=int,
    )
    parser.add_argument(
        "--wait",
        help="number of seconds to wait between retries if error from unshrtn service",
        default=wait,
        type=int,
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="files to read, if empty, stdin is used",
    )
    args = parser.parse_args()

    unshrtn_url = args.unshrtn
    retries = args.retries
    wait = args.wait
    pool = multiprocessing.Pool(args.pool_size)
    for line in pool.imap_unordered(
        rewrite_line,
        fileinput.input(files=args.files if len(args.files) > 0 else ("-",)),
    ):
        if line != "\n":
            print(line)


if __name__ == "__main__":
    main()
