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

def sleep_till(t):
    now = time.time()
    if now > t:
        return 
    secs = t - now + 5 # padded with 5 seconds to be safe
    logging.info("sleeping %s seconds for rate limiting" % secs)
    time.sleep(secs)

def search(q, max_id=None, rate_limit_remaining=None, rate_limit_reset=None):
    if rate_limit_remaining != None and rate_limit_remaining == 0:
        sleep_till(rate_limit_reset)
        rate_limit_remaining = None
        rate_limit_reset = None

    # figure out the search API call
    url = "https://api.twitter.com/1.1/search/tweets.json?q=%s" % q
    if max_id:
        url += "&max_id=%s" % max_id

    # twitter search api sometimes throws a 500, try 5 times, while
    # backing off and then give up

    count = 0
    while count <= 5:
        logging.info("fetching %s", url)
        resp, content = client.request(url)
        if resp.status == 200:
            break
        count += 1
        secs = count * 2
        logging.error("got error when fetching %s sleeping %s secs", url, secs)
        time.sleep(count * 2)

    if resp.status != 200:
        logging.fatal("couldn't get search results for %s" % url)
        sys.exit(1)

    # set rate limit info if not known
    if rate_limit_remaining == None:
        rate_limit_remaining = int(resp["x-rate-limit-remaining"])
        rate_limit_reset = int(resp["x-rate-limit-reset"])
    else:
        rate_limit_remaining -= 1

    # return an generator for each result
    results = json.loads(content)

    if not results.has_key("statuses"):
        print json.dumps(results, indent=2)
    for status in results["statuses"]:
        yield status
   
    # look for the next set of results
    if status:
        max_id = status["id_str"]
        for status in search(q, max_id, rate_limit_remaining, rate_limit_reset):
            yield status

def archive(statuses, filename):
    logging.info("writing tweets to %s" % filename)
    fh = open(filename, "a")
    for status in statuses:
        url = "http://twitter.com/%s/status/%s" % (status["user"]["screen_name"], status["id_str"])
        logging.info("archived %s", url)
        fh.write(json.dumps(status))
        fh.write("\n")

if __name__ == "__main__":
    q = sys.argv[1]
    log_filename = "%s.log" % q
    archive_filename = "%s.json" % q
    logging.basicConfig(filename=log_filename, level=logging.INFO)

    # try to pick up where we left off, by reading last tweet id
    # from the archive file
    max_id = None
    if os.path.isfile(archive_filename):
        for line in open(archive_filename):
            pass
        max_id = json.loads(line)["id_str"]
        logging.info("picking up where we left off with max_id=%s" % max_id)

    archive(search(q, max_id=max_id), archive_filename)
