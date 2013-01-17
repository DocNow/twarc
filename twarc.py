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

class Search:

    def __init__(self, q, since_id=None, max_id=None):
        self.q = q
        self.since_id = since_id
        self.max_id = max_id
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def run(self):
        found = True
        while found:
            found = False
            for status in self._do_search():
                found = True
                yield status

    def _do_search(self):
        """returns a page of search results from Twitter
        """
        logging.info("starting search for %s with max_id of %s" % (self.q, self.max_id))
        self.check_rate_limit()

        # do the api call
        url = "https://api.twitter.com/1.1/search/tweets.json?q=%s" % urllib.quote(self.q)
        if self.since_id:
            url += "&since_id=%s" % self.since_id
        if self.max_id:
            url += "&max_id=%s" % self.max_id
        resp, content = self.fetch(url)

        # set rate limit info if not known, or decrement our counter
        if self.rate_limit_remaining == None:
            self.rate_limit_remaining = int(resp["x-rate-limit-remaining"])
            self.rate_limit_reset = int(resp["x-rate-limit-reset"])
        else:
            self.rate_limit_remaining -= 1
       
        # set max_id appropriately for the next search results
        # and return page of results
        statuses = json.loads(content)["statuses"]

        # if we didn't get any new tweets return empty list
        new_max_id = int(statuses[-1]["id_str"]) + 1
        if self.max_id == new_max_id:
            logging.info("no new tweets with id < %s", self.max_id)
            return []

        self.max_id = new_max_id
        return statuses

    def check_rate_limit(self):
       if self.rate_limit_remaining != None and self.rate_limit_remaining == 0:
           now = time.time()
           if now < self.rate_limit_reset:
               # padded with 5 seconds to be safe
               secs = self.rate_limit_reset - now + 5 
               logging.info("sleeping %s seconds for rate limiting" % secs)
               time.sleep(secs)
           self.rate_limit_remaining = None
           self.rate_limit_reset = None

    def fetch(self, url, tries=5):
        count = 0
        while count <= tries:
            logging.info("fetching %s", url)
            resp, content = client.request(url)

            if resp.status == 200:
                return resp, content

            count += 1
            secs = count * 2
            logging.error("got error when fetching %s sleeping %s secs", url, secs)
            time.sleep(count * 2)

        if resp.status != 200:
            logging.fatal("couldn't get search results for %s" % url)
            sys.exit(1)

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

def archive(statuses, q):
    t = time.strftime("%Y%m%d%H%M%S", time.localtime())
    archive_filename = "%s-%s.json" % (q, t)
    logging.info("writing tweets to %s" % archive_filename)

    fh = open(archive_filename, "w")
    for status in statuses:
        url = "http://twitter.com/%s/status/%s" % (status["user"]["screen_name"], status["id_str"])
        logging.info("archived %s", url)
        fh.write(json.dumps(status))
        fh.write("\n")

if __name__ == "__main__":
    q = sys.argv[1]
    logging.basicConfig(filename="%s.log" % q, level=logging.INFO)
    since_id = most_recent_id(q)
    search = Search(q, since_id)
    archive(search.run(), q) 
