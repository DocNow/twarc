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

# TODO: add more shortener hosts as needed and send a pull-request plz!

shorteners = set([
    "1.usa.gov",
    "bit.ly",
    "fb.me",
    "goo.gl",
    "is.gd",
    "ow.ly"
    "t.co",
    "tinyurl.com",
    "wp.me",
])

cache = {}
for line in fileinput.input():
    tweet = json.loads(line)
    for url_dict in tweet["entities"]["urls"]:
        if "expanded_url" in url_dict:
            url = url_dict["expanded_url"]
        else:
            url = url_dict['url']

        u = urlparse.urlparse(url)
        if url in cache:
            unshortened_url = cache[url]
        elif u.netloc in shorteners:
            # for some reason goo.gl blocks when you try a HEAD request
            try:
                logging.info("looking up %s", url)
                if u.netloc == "goo.gl":
                    resp = requests.get(url)
                else:
                    resp = requests.head(url)
                if "Location" in resp.headers:
                    unshortened_url = resp.headers["Location"]
                else:
                    unshortened_url = url
            except Exception as e:
                logging.error("lookup failed for %s: %s", url, e)
        else:
            unshortened_url = url

        cache[url] = unshortened_url            
        logging.info("unshortened %s to %s", url, unshortened_url)
        url_dict['unshortened_url'] = unshortened_url

    print json.dumps(tweet).encode('utf8')
