#!/usr/bin/env python

"""
Unfortunately the "expanded_url" as supplied by Twitter aren't fully 
expanded past t.co.

unshorten.py will attempt to unshorten URLs and add them as the 
"unshortened_url" key to each url, and emit the tweet as JSON again on stdout. 

You'll need to `pip install leveldb` to get it to work since it creates a little
database of unshortened url mappings to prevent looking up the same short url
repeatedly.
"""

import json
import urllib
import leveldb
import logging
import urllib2
import urlparse
import fileinput
import multiprocessing

# number of urls to look up in parallel
POOL_SIZE = 10

logging.basicConfig(filename="unshorten.log", level=logging.INFO)
db = leveldb.LevelDB('unshorten.db')

def unshorten(url):
    unshortened_url = None
    try:
        return db.Get(url)
    except KeyError:
        try:
            resp = urllib2.urlopen(url, timeout=60)
            unshortened_url = resp.url.encode('utf8')
            db.Put(url, unshortened_url)
        except Exception as e:
            logging.error("lookup failed for %s: %s", url, e)
    except Exception as e:
        logging.error("leveldb Get error: %s", e)

    return unshortened_url

def rewrite_line(line):
    tweet = json.loads(line)

    # don't do the same work again
    if 'unshortened_url' in tweet:
        return tweet

    for url_dict in tweet["entities"]["urls"]:
        if "expanded_url" in url_dict:
            url = url_dict["expanded_url"]
        else:
            url = url_dict['url']

        unshortened_url = unshorten(url.encode('utf8'))

        # add new key to the json
        if unshortened_url:
            url_dict['unshortened_url'] = unshortened_url

    return tweet

def main():
    pool = multiprocessing.Pool(POOL_SIZE)
    for tweet in pool.imap_unordered(rewrite_line, fileinput.input()):
        print json.dumps(tweet).encode('utf8')

if __name__ == "__main__":
    main()
