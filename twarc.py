#!/usr/bin/env python

import os
import re
import sys
import json
import time
import config
import oauth2
import urllib
import logging

consumer = oauth2.Consumer(key=config.consumer_key, secret=config.consumer_secret)
token = oauth2.Token(config.access_token, config.access_token_secret)
client = oauth2.Client(consumer, token)

class RateLimiter:

    def __init__(self):
        self._ping()

    def check(self):
        if self.remaining == 0:
            now = time.time()
            if now < self.reset:
                # padded with 5 seconds just to be on the safe side
                secs = self.reset - now + 5 
                logging.info("sleeping %s seconds for rate limiting" % secs)
                time.sleep(secs)
        self._ping()

    def _ping(self):
        """fetches latest rate limits from Twitter
        """
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json?resources=search"
        response, content = client.request(url)
        result = json.loads(content)["resources"]["search"]["/search/tweets"]
        self.reset = result["reset"]
        self.remaining = result["remaining"]

def search(q, since_id=None, max_id=None):
    """returns a generator for *all* search results.
    """
    logging.info("starting search for %s with since_id=%s and max_id of %s" % (q, since_id, max_id))
    while True:
        results, max_id = search_result(q, since_id, max_id)
        if len(results) == 0:
            break
        for status in results:
            yield status

def search_result(q, since_id=None, max_id=None):
    """returns a single page of search results
    """
    # do the api call
    url = "https://api.twitter.com/1.1/search/tweets.json?q=%s" % urllib.quote(q)
    if since_id:
        url += "&since_id=%s" % since_id
    if max_id:
        url += "&max_id=%s" % max_id
    resp, content = fetch(url)

    statuses = json.loads(content)["statuses"]

    new_max_id = int(statuses[-1]["id_str"]) + 1
    if max_id == new_max_id:
        logging.info("no new tweets with id < %s", max_id)
        return [], max_id

    return statuses, new_max_id

def fetch(url, tries=5):
    if tries == 0:
        logging.error("unable to fetch %s - too many tries!", url)
        return None

    rate_limiter.check()
    logging.info("fetching %s", url)
    resp, content = client.request(url)

    if resp.status == 200:
        return resp, content

    secs =  (6 - tries) * 2
    logging.error("got error when fetching %s sleeping %s secs", url, secs)
    time.sleep(count * 2)

    return fetch(url, tries - 1)
 
def most_recent_id(q):
    last_archive_file = last_archive(q)
    if not last_archive_file:
        return None
    return json.loads(open(last_archive_file).readline())["id_str"]

def last_archive(q):
    other_archive_files = []
    for filename in os.listdir("."):
        if re.match("^%s-\d+\.json$" % q, filename):
            other_archive_files.append(filename)
    other_archive_files.sort()
    if len(other_archive_files) > 0:
        return other_archive_files[-1]
    return None

def archive(q, statuses):
    t = time.strftime("%Y%m%d%H%M%S", time.localtime())
    archive_filename = "%s-%s.json" % (q, t)
    logging.info("writing tweets to %s" % archive_filename)

    fh = open(archive_filename, "w")
    for status in statuses:
        url = "http://twitter.com/%s/status/%s" % (status["user"]["screen_name"], status["id_str"])
        logging.info("archived %s", url)
        fh.write(json.dumps(status))
        fh.write("\n")

rate_limiter = RateLimiter()

if __name__ == "__main__":
    q = sys.argv[1]
    logging.basicConfig(filename="%s.log" % q, level=logging.INFO)
    since_id = most_recent_id(q)
    archive(q, search(q, since_id)) 
