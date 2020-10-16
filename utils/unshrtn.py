#!/usr/bin/env python

"""
Unfortunately the "expanded_url" as supplied by Twitter aren't fully
expanded one hop past t.co.

unshrtn.py will attempt to completely unshorten URLs and add them as the
"unshortened_url" key to each url, and emit the tweet as JSON again on stdout.

This script starts 10 seaprate processes which talk to an instance of unshrtn
that is running:

    http://github.com/edsu/unshrtn

"""


import re
import json
import time
import urllib.request, urllib.parse, urllib.error
import logging
import argparse
import fileinput
import multiprocessing

# number of urls to look up in parallel
POOL_SIZE = 10
unshrtn_url = "http://localhost:3000"
retries = 2
wait = 15

logging.basicConfig(filename="unshorten.log", level=logging.INFO)


def unshorten_url(url):
    if url is None:
        return None

    # TODO: Worth providing some way for the user to specify specific hostnames they want to expand,
    # instead of assuming that all hostnames need expanding?
    if re.match(r"^https?://twitter.com/", url):
        return url

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

    for key in ["canonical", "long"]:
        if key in resp:
            return resp[key]

    return None


def rewrite_line(line):
    try:
        tweet = json.loads(line)
    except Exception as e:
        # garbage in, garbage out
        logging.error(e)
        return line

    # don't do the same work again
    if "unshortened_url" in tweet and tweet["unshortened_url"]:
        return line

    for url_dict in tweet["entities"]["urls"]:
        if "expanded_url" in url_dict:
            url = url_dict["expanded_url"]
        else:
            url = url_dict["url"]

        url_dict["unshortened_url"] = unshorten_url(url)

    tweet["user"]["unshortened_url"] = unshorten_url(tweet["user"]["url"])

    return json.dumps(tweet)


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
