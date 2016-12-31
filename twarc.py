#!/usr/bin/env python

from __future__ import print_function

__version__ = '1.0.2' # also in setup.py

import os
import re
import sys
import json
import time
import logging
import argparse
import datetime
import requests
import fileinput

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

commands = [
    "configure",
    'filter',
    'followers',
    'friends',
    'help',
    'hydrate',
    'retweets',
    'sample',
    'search',
    'timeline',
    'trends', 
    'users',
    'version',
]

def main():
    parser = get_argparser()
    args = parser.parse_args()

    command = args.command
    query = args.query or ""

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    if command == "version":
        print("twarc v%s" % __version__)
        sys.exit()
    elif command == "help" or not command:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    twarc search blacklivesmatter")
        sys.exit(1)

    t = Twarc(
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        access_token=args.access_token,
        access_token_secret=args.access_token_secret,
        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile
    )

    # calls that return tweets
    if command == "search":
        things = t.search(
            query,
            since_id=args.since_id,
            max_id=args.max_id,
            lang=args.lang,
            result_type=args.result_type,
            geocode=args.geocode
        )

    elif command == "filter":
        things = t.filter(
            track=query,
            follow=args.follow,
            locations=args.locations
        )
        
    elif command == "hydrate":
        input_iterator = fileinput.FileInput(
            query,
            mode='rU',
            openhook=fileinput.hook_compressed,
        )
        things = t.hydrate(input_iterator)

    elif command == "sample":
        things = t.sample()

    elif command == "timeline":
        if re.match('^[0-9]+$', query):
            things = t.timeline(user_id=query)
        else:
            things = t.timeline(screen_name=query)

    elif command == "retweets":
        things = t.retweets(query)

    elif command == "users":
        if os.path.isfile(query):
            iterator = fileinput.FileInput(
                query,
                mode='rU',
                openhook=fileinput.hook_compressed,
            )
            things = t.user_lookup(iterator=iterator)
        elif re.match('^[0-9,]+$', query):
            things = t.user_lookup(user_ids=query.split(","))
        else:
            things = t.user_lookup(screen_names=query.split(","))

    elif command == "followers":
        things = t.follower_ids(screen_name=query)

    elif command == "friends":
        things = t.friend_ids(screen_name=query)

    elif command == "trends":
        # lookup woeid for geo-coordinate if appropriate
        geo = re.match('^([0-9\-\.]+),([0-9\-\.]+)$', query)
        if geo:
            lat, lon = map(float, geo.groups())
            if lat > 180 or lat < -180 or lon > 180 or lon < -180:
                parser.error('LAT and LONG must be within [-180.0, 180.0]')
            places = list(t.trends_closest(lat, lon))
            if len(places) == 0:
                parser.error("Couldn't find WOE ID for %s" % query)
            query = places[0]["woeid"]

        if not query:
            things = t.trends_available()
        else:
            trends = t.trends_place(query)
            if trends:
                things = trends[0]['trends']

    elif command == "configure":
        t.input_keys()
        sys.exit()

    else:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    twarc search blacklivesmatter")
        sys.exit(1)

    for thing in things:
        kind_of = type(thing)
        if kind_of == int:
            # user ids
            print(thing)
            logging.info("archived %s" % thing)
        elif 'id_str' in thing:
            # tweets and users
            print(json.dumps(thing))
            logging.info("archived %s", thing['id_str'])
        elif 'woeid' in thing:
            # places
            print(json.dumps(thing))
        elif 'tweet_volume' in thing:
            # trends
            print(json.dumps(thing))
        elif 'limit' in thing:
            # rate limits
            t = datetime.datetime.utcfromtimestamp(
                float(thing['limit']['timestamp_ms']) / 1000)
            t = t.isoformat("T") + "Z"
            logging.warn("%s tweets undelivered at %s",
                         thing['limit']['track'], t)
            if args.warnings:
                print(json.dumps(thing))
        elif 'warning' in thing:
            # other warnings
            logging.warn(thing['warning']['message'])
            if args.warnings:
                print(json.dumps(thing))


def get_argparser():
    """
    Get the command line argument parser.
    """
    
    config = os.path.join(os.path.expanduser("~"), ".twarc")

    parser = argparse.ArgumentParser("twarc")
    parser.add_argument('command', choices=commands)
    parser.add_argument('query', nargs='?', default=None)
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
    parser.add_argument('--config', default=config,
                        help="Config file containing Twitter keys and secrets")
    parser.add_argument('--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('--warnings', action='store_true',
                        help="Include warning messages in output")
    parser.add_argument("--connection_errors", type=int, default="0",
                        help="Number of connection errors before giving up")
    parser.add_argument("--http_errors", type=int, default="0",
                        help="Number of http errors before giving up")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--result_type", dest="result_type",
                        choices=["mixed", "recent", "popular"],
                        default="recent", help="search result type")
    parser.add_argument("--lang", dest="lang",
                        help="limit to ISO 639-1 language code"),
    parser.add_argument("--geocode", dest="geocode",
                        help="limit by latitude,longitude,radius")
    parser.add_argument("--locations", dest="locations",
                        help="limit filter stream to location(s)")
    parser.add_argument("--follow", dest="follow",
                        help="limit filter to tweets from given user id(s)")

    return parser


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
                logging.warn("%s from Twitter API, sleeping %s",
                             resp.status_code, seconds)
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
        ConnectionError = None

    def new_f(self, *args, **kwargs):
        # Only handle if pyOpenSSL is installed.
        if ConnectionError:
            try:
                return f(self, *args, **kwargs)
            except ConnectionError as e:
                logging.warn("caught connection reset error: %s", e)
                self.connect()
                return f(self, *args, **kwargs)
        else:
            return f(self, *args, **kwargs)
    return new_f


def catch_timeout(f):
    """
    A decorator to handle read timeouts from Twitter.
    """
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except requests.exceptions.ReadTimeout as e:
            logging.warn("caught read timeout: %s", e)
            self.connect()
            return f(self, *args, **kwargs)
    return new_f


def catch_gzip_errors(f):
    """
    A decorator to handle gzip encoding errors which have been known to
    happen during hydration.
    """
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except requests.exceptions.ContentDecodingError as e:
            logging.warn("caught gzip error: %s", e)
            self.connect()
            return f(self, *args, **kwargs)
    return new_f



class Twarc(object):
    """
    Twarc allows you retrieve data from the Twitter API. Each method
    is an iterator that runs to completion, and handles rate limiting so 
    that it will go to sleep when Twitter tells it to, and wake back up
    when it is able to retrieve data from the API again.
    """

    def __init__(self, consumer_key=None, consumer_secret=None,
                 access_token=None, access_token_secret=None, 
                 connection_errors=0, http_errors=0, config=None, 
                 profile="main"):
        """
        Instantiate a Twarc instance. If keys aren't set we'll try to 
        discover them in the environment or a supplied profile.
        """

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.connection_errors = connection_errors
        self.http_errors = http_errors
        self.config = config
        self.profile = profile
        self.client = None
        self.last_response = None

        self.check_keys()
        self.connect()

    def search(self, q, max_id=None, since_id=None, lang=None,
               result_type='recent', geocode=None):
        """
        Pass in a query with optional max_id, min_id, lang or geocode
        and get back an iterator for decoded tweets. Defaults to recent (i.e.
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
        if geocode is not None:
            params['geocode'] = geocode

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

    def timeline(self, user_id=None, screen_name=None, max_id=None,
                 since_id=None):
        """
        Returns a collection of the most recent tweets posted
        by the user indicated by the user_id or screen_name parameter.
        Provide a user_id or screen_name.
        """
        # Strip if screen_name is prefixed with '@'
        if screen_name:
            screen_name = screen_name.lstrip('@')
        id = screen_name or user_id
        id_type = "screen_name" if screen_name else "user_id"
        logging.info("starting user timeline for user %s", id)
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {"count": 200, id_type: id}

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id

            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.info("no timeline available for %s", id)
                    break
                raise e

            statuses = resp.json()

            if len(statuses) == 0:
                logging.info("no new tweets matching %s", params)
                break

            for status in statuses:
                # If you request an invalid user_id, you may still get
                # results so need to check.
                if not user_id or user_id == status.get("user",
                                                        {}).get("id_str"):
                    yield status

            max_id = str(int(status["id_str"]) - 1)

    def user_lookup(self, screen_names=None, user_ids=None, iterator=None):
        """
        A generator that returns users for supplied screen_names,
        user_ids or an iterator of user_ids.
        """
        if screen_names:
            screen_names = [s.lstrip('@') for s in screen_names]
        ids = screen_names or user_ids
        id_type = "screen_name" if screen_names else "user_id"

        if not iterator:
            iterator = iter(ids)
      
        # TODO: this is similar to hydrate, maybe they could share code?

        lookup_ids = []
        def do_lookup():
            ids_str = ",".join(lookup_ids)
            logging.info("looking up users %s", ids_str)
            url = 'https://api.twitter.com/1.1/users/lookup.json'
            params = {id_type: ids_str}
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.warn("no users matching %s", ids_str)
                raise e
            return resp.json()

        for id in iterator:
            if len(lookup_ids) == 100:
                for u in do_lookup():
                    yield u
                lookup_ids = []
            else:
                lookup_ids.append(id.strip())

        if len(lookup_ids) > 0:
            for u in do_lookup():
                yield u

    def follower_ids(self, screen_name):
        """
        Returns Twitter user id lists for the specified screen_name's
        followers.
        """
        screen_name = screen_name.lstrip('@')
        url = 'https://api.twitter.com/1.1/followers/ids.json'
        params = {'screen_name': screen_name, 'cursor': -1}
        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.info("no users matching %s", screen_name)
                raise e
            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield user_id
            params['cursor'] = user_ids['next_cursor']

    def friend_ids(self, screen_name):
        """
        Returns Twitter user id lists for the specified screen_name's friends
        (following).
        """
        screen_name = screen_name.lstrip('@')
        url = 'https://api.twitter.com/1.1/friends/ids.json'
        params = {'screen_name': screen_name, 'cursor': -1}
        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.info("no users matching %s", screen_name)
                raise e
            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield user_id
            params['cursor'] = user_ids['next_cursor']

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
                for line in resp.iter_lines(chunk_size=1024):
                    if not line:
                        logging.info("keep-alive")
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        logging.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                logging.error("caught http error %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many errors")
                    raise e
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
                logging.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many exceptions")
                    raise e
                t = errors * 1
                logging.error(e)
                logging.info("sleeping %s", t)
                time.sleep(t)

    def sample(self):
        """
        Returns a small random sample of all public statuses. The Tweets
        returned by the default access level are the same, so if two different
        clients connect to this endpoint, they will see the same Tweets.
        """
        url = 'https://stream.twitter.com/1.1/statuses/sample.json'
        params = {"stall_warning": True}
        headers = {'accept-encoding': 'deflate, gzip'}
        errors = 0
        while True:
            try:
                logging.info("connecting to sample stream")
                resp = self.post(url, params, headers=headers, stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=512):
                    if line == "":
                        logging.info("keep-alive")
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        logging.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                logging.error("caught http error %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many errors")
                    raise e
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
                logging.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many errors")
                    raise e
                t = errors * 1
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

    def retweets(self, tweet_id):
        """
        Retrieves up to the last 100 retweets for the provided
        tweet.
        """
        logging.info("retrieving retweets of %s", tweet_id)
        url = "https://api.twitter.com/1.1/statuses/retweets/{}.json".format(tweet_id)

        resp = self.get(url)
        for tweet in resp.json():
            yield tweet

    def trends_available(self):
        """
        Returns a list of regions for which Twitter tracks trends.
        """
        url = 'https://api.twitter.com/1.1/trends/available.json'
        try:
            resp = self.get(url)
        except requests.exceptions.HTTPError as e:
            raise e
        return resp.json()

    def trends_place(self, woeid, exclude=None):
        """
        Returns recent Twitter trends for the specified WOEID. If
        exclude == 'hashtags', Twitter will remove hashtag trends from the
        response.
        """
        url = 'https://api.twitter.com/1.1/trends/place.json'
        params = {'id': woeid}
        if exclude:
            params['exclude'] = exclude
        try:
            resp = self.get(url, params=params, allow_404=True)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.info("no region matching WOEID %s", woeid)
            raise e
        return resp.json()

    def trends_closest(self, lat, lon):
        """
        Returns the closest regions for the supplied lat/lon.
        """
        url = 'https://api.twitter.com/1.1/trends/closest.json'
        params = {'lat': lat, 'long': lon}
        try:
            resp = self.get(url, params=params)
        except requests.exceptions.HTTPError as e:
            raise e
        return resp.json()

    @rate_limit
    @catch_conn_reset
    @catch_timeout
    @catch_gzip_errors
    def get(self, *args, **kwargs):
        # Pass allow 404 to not retry on 404
        allow_404 = kwargs.pop('allow_404', False)
        connection_error_count = kwargs.pop('connection_error_count', 0)
        try:
            r = self.last_response = self.client.get(*args, **kwargs)
            # this has been noticed, believe it or not
            # https://github.com/edsu/twarc/issues/75
            if r.status_code == 404 and not allow_404:
                logging.warn("404 from Twitter API! trying again")
                time.sleep(1)
                r = self.get(*args, **kwargs)
            return r
        except requests.exceptions.ConnectionError as e:
            connection_error_count += 1
            logging.error("caught connection error %s on %s try", e, connection_error_count)
            if self.connection_errors and connection_error_count == self.connection_errors:
                logging.error("received too many connection errors")
                raise e
            else:
                self.connect()
                kwargs['connection_error_count'] = connection_error_count
                return self.get(*args, **kwargs)

    @rate_limit
    @catch_conn_reset
    @catch_timeout
    @catch_gzip_errors
    def post(self, *args, **kwargs):
        connection_error_count = kwargs.pop('connection_error_count', 0)
        try:
            self.last_response = self.client.post(*args, **kwargs)
            return self.last_response
        except requests.exceptions.ConnectionError as e:
            connection_error_count += 1
            logging.error("caught connection error %s on %s try", e, connection_error_count)
            if self.connection_errors and connection_error_count == self.connection_errors:
                logging.error("received too many connection errors")
                raise e
            else:
                self.connect()
                kwargs['connection_error_count'] = connection_error_count
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

    def check_keys(self):
        """
        Get the Twitter API keys. Order of precedence is command line,
        environment, config file.
        """
        env = os.environ.get
        if not self.consumer_key:
            self.consumer_key = env('CONSUMER_KEY')
        if not self.consumer_secret: 
            self.consumer_secret = env('CONSUMER_SECRET')
        if not self.access_token: 
            self.access_token = env('ACCESS_TOKEN')
        if not self.access_token_secret: 
            self.access_token_secret = env('ACCESS_TOKEN_SECRET')
        
        if self.config and not (self.consumer_key and self.consumer_secret 
                and self.access_token and self.access_token_secret):
            credentials = self.load_config()
            if credentials:
                self.consumer_key = credentials['consumer_key']
                self.consumer_secret = credentials['consumer_secret']
                self.access_token = credentials['access_token']
                self.access_token_secret = credentials['access_token_secret']
            else:
                self.input_keys()

    def load_config(self):
        path = self.config
        profile = self.profile
        if not os.path.isfile(path):
            return {}

        config = configparser.ConfigParser()
        config.read(self.config)
        data = {}
        for key in ['access_token', 'access_token_secret',
                    'consumer_key', 'consumer_secret']:
            try:
                data[key] = config.get(profile, key)
            except configparser.NoSectionError:
                sys.exit("no such profile %s in %s" % (profile, path))
            except configparser.NoOptionError:
                sys.exit("missing %s from profile %s in %s" % (
                         key, profile, path))
        return data

    def save_config(self):
        if not self.config:
            return
        config = configparser.ConfigParser()
        config.add_section(self.profile)
        config.set(self.profile, 'consumer_key', self.consumer_key)
        config.set(self.profile, 'consumer_secret', self.consumer_secret)
        config.set(self.profile, 'access_token', self.access_token)
        config.set(self.profile, 'access_token_secret', 
                   self.access_token_secret)
        with open(self.config, 'w') as config_file:
            config.write(config_file)

    def input_keys(self):
        print("Please enter Twitter authentication credentials")

        config = self.load_config()
        def i(name):
            prompt = name.replace('_', ' ')
            if name in config:
                prompt += ' [%s]' % config[name]
            return get_input(prompt + ": ") or config.get(name)

        self.consumer_key = i('consumer_key') 
        self.consumer_secret = i('consumer_secret')
        self.access_token = i('access_token')
        self.access_token_secret = i('access_token_secret')
        self.save_config()


if __name__ == "__main__":
    main()
