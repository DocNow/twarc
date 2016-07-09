#!/usr/bin/env python

"""
Unfortunately the "expanded_url" as supplied by Twitter aren't fully
expanded one hop past t.co.

unshorten.py will attempt to completely unshorten URLs and add them as the
"unshortened_url" key to each url, and emit the tweet as JSON again on stdout.

This script starts 10 seaprate processes which talk to an instance of unshrtn
that is running.

    http://github.com/edsu/unshrtn

"""
from __future__ import print_function

import json
import urllib
import logging
import fileinput
import multiprocessing
import argparse

# number of urls to look up in parallel
POOL_SIZE = 10
unshrtn_url = "http://localhost:3000"

logging.basicConfig(filename="unshorten.log", level=logging.INFO)


def rewrite_line(line):
    tweet = json.loads(line)

    # don't do the same work again
    if 'unshortened_url' in tweet and tweet['unshortened_url']:
        return line

    for url_dict in tweet["entities"]["urls"]:
        if "expanded_url" in url_dict:
            url = url_dict["expanded_url"]
        else:
            url = url_dict['url']

        url = url.encode('utf8')
        u = '{}/?{}'.format(unshrtn_url, urllib.urlencode({'url': url}))
        try:
            resp = json.loads(urllib.urlopen(u).read())
            if resp['long']:
                url_dict['unshortened_url'] = resp['long']
        except Exception as e:
            logging.error("http error: %s when looking up %s", e, url)
            return line

    return json.dumps(tweet)


def main():
    global unshrtn_url
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool-size', help='number of urls to look up in parallel', default=POOL_SIZE, type=int)
    parser.add_argument('--unshrtn', help='url of the unshrtn service', default=unshrtn_url)
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    unshrtn_url = args.unshrtn
    pool = multiprocessing.Pool(args.pool_size)
    for line in pool.imap_unordered(rewrite_line, fileinput.input(files=args.files if len(args.files) > 0 else ('-',))):
        if line != "\n": print(line)

if __name__ == "__main__":
    main()
