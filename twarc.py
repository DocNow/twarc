#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import json
import time
import logging
import argparse
import requests

from requests_oauthlib import OAuth1Session

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
else:
    # Python 3
    get_input = input


def geo(value):
    return '-74,40,-73,41'


def main():
    """
    The twarc command line.
    """
    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--search", dest="search",
                        help="search for tweets matching a query")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--result_type", dest="result_type",
                        choices=["mixed", "recent", "popular"],
                        default="recent", help="search result type")
    parser.add_argument("--lang", dest="lang",
                        help="limit to ISO 639-1 language code"),
    parser.add_argument("--track", dest="track",
                        help="stream tweets matching track filter")
    parser.add_argument("--follow", dest="follow",
                        help="stream tweets from user ids")
    parser.add_argument("--locations", dest="locations",
                        help="stream tweets from a particular location")
    parser.add_argument("--hydrate", dest="hydrate",
                        help="rehydrate tweets from a file of tweet ids")
    parser.add_argument("--log", dest="log",
                        default="twarc.log", help="log file")
    parser.add_argument("--consumer_key",
                        default=None, help="Twitter API consumer key")
    parser.add_argument("--consumer_secret",
                        default=None, help="Twitter API consumer secret")
    parser.add_argument("--access_token",
                        default=None, help="Twitter API access key")
    parser.add_argument("--access_token_secret",
                        default=None, help="Twitter API access token secret")
    parser.add_argument('-c', '--config',
                        default=default_config_filename(),
                        help="Config file containing Twitter keys and secrets")
    parser.add_argument('-p', '--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('-w', '--warnings', action='store_true', 
                        help="Include warning messages in output")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    consumer_key = args.consumer_key or os.environ.get('CONSUMER_KEY')
    consumer_secret = args.consumer_secret or os.environ.get('CONSUMER_SECRET')
    access_token = args.access_token or os.environ.get('ACCESS_TOKEN')
    access_token_secret = args.access_token_secret or os.environ.get("ACCESS_TOKEN_SECRET")

    if not (consumer_key and consumer_secret and
            access_token and access_token_secret):
        credentials = load_config(args.config, args.profile)
        if credentials:
            consumer_key = credentials['consumer_key']
            consumer_secret = credentials['consumer_secret']
            access_token = credentials['access_token']
            access_token_secret = credentials['access_token_secret']
        else:
            print("Please enter Twitter authentication credentials")
            consumer_key = get_input('consumer key: ')
            consumer_secret = get_input('consumer secret: ')
            access_token = get_input('access_token: ')
            access_token_secret = get_input('access token secret: ')
            save_keys(args.profile, consumer_key, consumer_secret,
                      access_token, access_token_secret)

    t = Twarc(consumer_key=consumer_key,
              consumer_secret=consumer_secret,
              access_token=access_token,
              access_token_secret=access_token_secret)

    if args.search:
        tweets = t.search(
            args.search,
            since_id=args.since_id,
            max_id=args.max_id,
            lang=args.lang,
            result_type=args.result_type,
        )
    elif args.track or args.follow or args.locations:
        tweets = t.filter(track=args.track, follow=args.follow,
                locations=args.locations)
    elif args.hydrate:
        tweets = t.hydrate(open(args.hydrate, 'rU'))
    else:
        raise argparse.ArgumentTypeError(
            "must supply one of: --search --stream or --hydrate")

    # iterate through the tweets and write them to stdout
    for tweet in tweets:
        
        # include warnings in output only if they asked for it
        if 'id_str' in tweet or args.warnings:
            print(json.dumps(tweet))

        # add some info to the log
        if "id_str" in tweet:
            logging.info("archived https://twitter.com/%s/status/%s", tweet['user']['screen_name'], tweet["id_str"])
        elif 'limit' in tweet:
            logging.warn("%s tweets undelivered", tweet["limit"]["track"])
        elif 'warning' in tweet:
            logging.warn(tweet['warning']['message'])
        else:
            logging.warn(json.dumps(tweet))


def load_config(filename, profile):
    if not os.path.isfile(filename):
        return None
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in ['access_token', 'access_token_secret', 'consumer_key', 'consumer_secret']:
        try:
            data[key] = config.get(profile, key)
        except configparser.NoSectionError:
            sys.exit("no such profile %s in %s" % (profile, filename))
        except configparser.NoOptionError:
            sys.exit("missing %s from profile %s in %s" % (key, profile, filename))
    return data


def save_config(filename, profile,
                consumer_key, consumer_secret,
                access_token, access_token_secret):
    config = configparser.ConfigParser()
    config.add_section(profile)
    config.set(profile, 'consumer_key', consumer_key)
    config.set(profile, 'consumer_secret', consumer_secret)
    config.set(profile, 'access_token', access_token)
    config.set(profile, 'access_token_secret', access_token_secret)
    with open(filename, 'w') as config_file:
        config.write(config_file)


def default_config_filename():
    """
    Return the default filename for storing Twitter keys.
    """
    home = os.path.expanduser("~")
    return os.path.join(home, ".twarc")


def save_keys(profile, consumer_key, consumer_secret,
              access_token, access_token_secret):
    """
    Save keys to ~/.twarc
    """
    filename = default_config_filename()
    save_config(filename, profile,
                consumer_key, consumer_secret,
                access_token, access_token_secret)
    print("Keys saved to", filename)


def rate_limit(f):
    """
    A decorator to handle rate limiting from the Twitter API. If
    a rate limit error is encountered we will sleep until we can
    issue the API call again.
    """
    def new_f(*args, **kwargs):
        errors = 0
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                errors = 0
                return resp
            elif resp.status_code == 429:
                reset = int(resp.headers['x-rate-limit-reset'])
                now = time.time()
                seconds = reset - now + 10
                if seconds < 1:
                    seconds = 10
                logging.warn("rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            elif resp.status_code >= 500:
                errors += 1
                if errors > 30:
                    logging.warn("too many errors from Twitter, giving up")
                    resp.raise_for_status()
                seconds = 60 * errors
                logging.warn("%s from Twitter API, sleeping %s", resp.status_code, seconds)
                time.sleep(seconds)
            else:
                resp.raise_for_status()
    return new_f


def catch_conn_reset(f):
    """
    A decorator to handle connection reset errors even ones from pyOpenSSL
    until https://github.com/edsu/twarc/issues/72 is resolved
    """
    try:
        import OpenSSL
        ConnectionError = OpenSSL.SSL.SysCallError
    except:
        ConnectionError = requests.exceptions.ConnectionError
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except ConnectionError:
            self.connect()
            return f(self, *args, **kwargs)
    return new_f


class Twarc(object):
    """
    Your friendly neighborhood Twitter archiving class. Twarc allows
    you to search for existing tweets, stream live tweets that match
    a filter query and lookup (hdyrate) a list of tweet ids.

    Each method search, stream and hydrate returns a tweet iterator which
    allows you to do what you want with the data. Twarc handles rate limiting
    in the API, so it will go to sleep when Twitter tells it to, and wake back
    up when it is able to get more data from the API.
    """

    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret):
        """
        Instantiate a Twarc instance. Make sure your environment variables
        are set.
        """

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.client = None
        self.last_response = None
        self.connect()

    def search(self, q, max_id=None, since_id=None, lang=None,
               result_type='recent'):
        """
        Pass in a query with optional max_id, min_id or lang and get
        back an iterator for decoded tweets. Defaults to recent (i.e.
        not mixed, the API default, or popular) tweets.
        """
        logging.info("starting search for %s", q)
        url = "https://api.twitter.com/1.1/search/tweets.json"
        params = {
            "count": 100,
            "q": q
        }
        if lang is not None:
            params['lang'] = lang
        if result_type in ['mixed', 'recent', 'popular']:
            params['result_type'] = result_type
        else:
            params['result_type'] = 'recent'

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id

            resp = self.get(url, params=params)
            statuses = resp.json()["statuses"]

            if len(statuses) == 0:
                logging.info("no new tweets matching %s", params)
                break

            for status in statuses:
                yield status

            max_id = str(int(status["id_str"]) - 1)

    def filter(self, track=None, follow=None, locations=None):
        """
        Returns an iterator for tweets that match a given filter track from
        the livestream of tweets happening right now.
        """
        if locations is not None:
            if type(locations) == list:
                locations = ','.join(locations)
            locations = locations.replace('\\', '')

        url = 'https://stream.twitter.com/1.1/statuses/filter.json'
        params = {"stall_warning": True}
        if track:
            params["track"] = track
        if follow:
            params["follow"] = follow
        if locations:
            params["locations"] = locations
        headers = {'accept-encoding': 'deflate, gzip'}
        errors = 0
        while True:
            try:
                logging.info("connecting to filter stream for %s", params)
                resp = self.post(url, params, headers=headers, stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=512):
                    if not line:
                        logging.info("keep-alive")
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        logging.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                logging.error(e)
                if e.response.status_code == 420:
                    t = errors * 60
                    logging.info("sleeping %s", t)
                    time.sleep(t)
                else:
                    t = errors * 5
                    logging.info("sleeping %s", t)
                    time.sleep(t)
            except Exception as e:
                errors += 1
                t = errors * 1
                logging.error(e)
                logging.info("sleeping %s", t)
                time.sleep(t)

    def hydrate(self, iterator):
        """
        Pass in an iterator of tweet ids and get back an iterator for the
        decoded JSON for each corresponding tweet.
        """
        ids = []
        url = "https://api.twitter.com/1.1/statuses/lookup.json"

        # lookup 100 tweets at a time
        for tweet_id in iterator:
            tweet_id = tweet_id.strip()  # remove new line if present
            ids.append(tweet_id)
            if len(ids) == 100:
                logging.info("hydrating %s ids", len(ids))
                resp = self.post(url, data={"id": ','.join(ids)})
                tweets = resp.json()
                tweets.sort(key=lambda t: t['id_str'])
                for tweet in tweets:
                    yield tweet
                ids = []

        # hydrate any remaining ones
        if len(ids) > 0:
            logging.info("hydrating %s", ids)
            resp = self.client.post(url, data={"id": ','.join(ids)})
            for tweet in resp.json():
                yield tweet

    @rate_limit
    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            r = self.last_response = self.client.get(*args, **kwargs)
            # this has been noticed, believe it or not
            # https://github.com/edsu/twarc/issues/75
            if r.status_code == 404:
                logging.warn("404 from Twitter API! trying again")
                time.sleep(1)
                r = self.get(*args, **kwargs)
            return r
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self.connect()
            return self.get(*args, **kwargs)

    @rate_limit
    @catch_conn_reset
    def post(self, *args, **kwargs):
        try:
            self.last_response = self.client.post(*args, **kwargs)
            return self.last_response
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self.connect()
            return self.post(*args, **kwargs)

    def connect(self):
        """
        Sets up the HTTP session to talk to Twitter. If one is active it is 
        closed and another one is opened.
        """
        if self.client:
            logging.info("closing existing http session")
            self.client.close()
        if self.last_response:
            logging.info("closing last response")
            self.last_response.close()
        logging.info("creating http session")
        self.client = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )

if __name__ == "__main__":
    main()
