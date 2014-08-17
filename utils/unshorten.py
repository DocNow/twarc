#!/usr/bin/env python

"""
Unfortunately the "expanded_url" as supplied by Twitter aren't fully 
expanded past t.co.

unshorten.py will attempt to unshorten URLs and add them as the 
"unshortened_url" key to each url, and emit the tweet as JSON again on stdout. 
"""

import json
import logging
import requests
import fileinput
import urlparse

logging.basicConfig(filename="unshorten.log", level=logging.INFO)

cache = {}
def unshorten(url):
    if url in cache:
        return cache[url]
    try:
        # let requests handle redirects
        resp = requests.get(url)
        cache[url] = resp.url
        return unshorten(resp.url)
    except Exception as e:
        logging.error("lookup failed for %s: %s", url, e)
        return url


def main():
    for line in fileinput.input():
        tweet = json.loads(line)
        for url_dict in tweet["entities"]["urls"]:
            if "expanded_url" in url_dict:
                url = url_dict["expanded_url"]
            else:
                url = url_dict['url']

            unshortened_url = unshorten(url)
            logging.info("unshortened %s to %s", url, unshortened_url)

            # add new key to the json
            url_dict['unshortened_url'] = unshortened_url

        print json.dumps(tweet).encode('utf8')

if __name__ == "__main__":
    main()
