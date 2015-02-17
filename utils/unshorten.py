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

# number of urls to look up in parallel
POOL_SIZE = 10

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
        u = 'http://localhost:3000/?' + urllib.urlencode({'url': url})
        try:
            resp = json.loads(urllib.urlopen(u).read())
            if resp['long']:
                url_dict['unshortened_url'] = resp['long']
        except Exception as e:
            logging.error("http error: %s when looking up %s", e, url)
            return line

    return json.dumps(tweet)

def main():
    pool = multiprocessing.Pool(POOL_SIZE)
    for line in pool.imap_unordered(rewrite_line, fileinput.input()):
        if line != "\n": print(line)

if __name__ == "__main__":
    main()
