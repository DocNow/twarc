#!/usr/bin/env python

import os
import sys
import json
import time
import config
import oauth2
import logging

consumer = oauth2.Consumer(key=config.consumer_key, secret=config.consumer_secret)
token = oauth2.Token(config.access_token, config.access_token_secret)
client = oauth2.Client(consumer, token)

class Search:

    def __init__(self, q, max_id=None):
        self.q = q
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
        url = "https://api.twitter.com/1.1/search/tweets.json?q=%s" % self.q
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
        self.max_id = int(statuses[-1]["id_str"]) + 1

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

def archive(statuses, filename):
    logging.info("writing tweets to %s" % filename)
    fh = open(filename, "a")
    for status in statuses:
        url = "http://twitter.com/%s/status/%s" % (status["user"]["screen_name"], status["id_str"])
        logging.info("archived %s", url)
        fh.write(json.dumps(status))
        fh.write("\n")

def last_id(archive_filename):
    max_id = None
    if os.path.isfile(archive_filename):
        # skip to the end of the file
        for line in open(archive_filename):
            pass
        if line:
            max_id = int(json.loads(line)["id_str"]) + 1
    return max_id

if __name__ == "__main__":
    q = sys.argv[1]
    log_filename = "%s.log" % q
    logging.basicConfig(filename=log_filename, level=logging.INFO)

    archive_filename = "%s.json" % q
    max_id = last_id(archive_filename)

    search = Search(q, max_id)
    archive(search.run(), archive_filename)
