#!/usr/bin/env python

from __future__ import print_function

__version__ = '0.8.2' # also in setup.py

import fileinput
import os
import sys
import json
import time
import logging
import argparse
import datetime
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


def main():
    """
    The twarc command line.
    """
    parser = argparse.ArgumentParser("twarc")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {version}'.format(
                            version=__version__))
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
    parser.add_argument("--geocode", dest="geocode",
                        help="limit by latitude,longitude,radius")
    parser.add_argument("--track", dest="track",
                        help="stream tweets matching track filter")
    parser.add_argument("--follow", dest="follow",
                        help="stream tweets from user ids")
    parser.add_argument("--locations", dest="locations",
                        help="stream tweets from a particular location")
    parser.add_argument("--sample", action="store_true",
                        help="stream sample live tweets")
    parser.add_argument("--timeline", dest="timeline",
                        help="get user timeline for a screen name")
    parser.add_argument("--timeline_user_id", dest="timeline_user_id",
                        help="get user timeline for a user id")
    parser.add_argument("--lookup_screen_names", dest="lookup_screen_names",
                        nargs='+', help="look up users by screen name; \
                                         returns user objects")
    parser.add_argument("--lookup_user_ids", dest="lookup_user_ids", nargs='+',
                        help="look up users by user id; returns user objects")
    parser.add_argument("--follower_ids", dest="follower_ids", nargs=1,
                        help="retrieve follower lists; returns follower ids")
    parser.add_argument("--friend_ids", dest="friend_ids", nargs=1,
                        help="retrieve friend (following) list; returns friend ids")
    parser.add_argument("--hydrate", action="append", dest="hydrate",
                        help="rehydrate tweets from a file of tweet ids, \
                              use - for stdin")
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
    parser.add_argument("--connection_errors", type=int, default="0",
                        help="Number of connection errors before giving up. Default is to keep trying.")
    parser.add_argument("--http_errors", type=int, default="0",
                        help="Number of http errors before giving up. Default is to keep trying.")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    consumer_key = args.consumer_key or os.environ.get('CONSUMER_KEY')
    consumer_secret = args.consumer_secret or os.environ.get('CONSUMER_SECRET')
    access_token = args.access_token or os.environ.get('ACCESS_TOKEN')
    access_token_secret = args.access_token_secret or os.environ.get('ACCESS_TOKEN_SECRET')

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
              access_token_secret=access_token_secret,
              connection_errors=args.connection_errors,
              http_errors=args.http_errors)

    tweets = []
    users = []
    user_ids = []

    # Calls that return tweets
    if args.search or args.geocode:
        tweets = t.search(
            args.search,
            since_id=args.since_id,
            max_id=args.max_id,
            lang=args.lang,
            result_type=args.result_type,
            geocode=args.geocode
        )
    elif args.track or args.follow or args.locations:
        tweets = t.filter(track=args.track, follow=args.follow,
                          locations=args.locations)
    elif args.hydrate:
        input_iterator = fileinput.FileInput(
            args.hydrate,
            mode='rU',
            openhook=fileinput.hook_compressed,
        )
        tweets = t.hydrate(input_iterator)
    elif args.sample:
        tweets = t.sample()
    elif args.timeline:
        tweets = t.timeline(screen_name=args.timeline)
    elif args.timeline_user_id:
        tweets = t.timeline(user_id=args.timeline_user_id)

    # Calls that return user profile objects
    elif args.lookup_user_ids:
        users = t.user_lookup(user_ids=args.lookup_user_ids)
    elif args.lookup_screen_names:
        users = t.user_lookup(screen_names=args.lookup_screen_names)

    # Calls that return lists of user ids
    elif args.follower_ids:
        # Note: only one at a time, so assume exactly one
        user_ids = t.follower_ids(screen_name=args.follower_ids[0])
    elif args.friend_ids:
        # Note: same here, only one at a time, so assume exactly one
        user_ids = t.friend_ids(screen_name=args.friend_ids[0])

    else:
        raise argparse.ArgumentTypeError(
            'must supply one of:  --search --track --follow --locations'
            ' --timeline --timeline_user_id'
            ' --lookup_screen_names --lookup_user_ids'
            ' --sample --hydrate')

    # iterate through the tweets and write them to stdout
    for tweet in tweets:
        # include warnings in output only if they asked for it
        if 'id_str' in tweet or args.warnings:
            print(json.dumps(tweet))

        # add some info to the log
        if 'id_str' in tweet:
            if 'user' in tweet:
                logging.info("archived https://twitter.com/%s/status/%s",
                             tweet['user']['screen_name'], tweet['id_str'])
        elif 'limit' in tweet:
            t = datetime.datetime.utcfromtimestamp(
                float(tweet['limit']['timestamp_ms']) / 1000)
            t = t.isoformat("T") + "Z"
            logging.warn("%s tweets undelivered at %s",
                         tweet['limit']['track'], t)
        elif 'warning' in tweet:
            logging.warn(tweet['warning']['message'])
        else:
            logging.warn(json.dumps(tweet))

    # iterate through the user objects and write them to stdout
    for user in users:
        # include warnings in output only if they asked for it
        if 'id_str' in user or args.warnings:
            print(json.dumps(user))

            # add some info to the log
            if 'screen_name' in user:
                logging.info("archived user profile for @%s / id_str=%s",
                             user['screen_name'], user['id_str'])
        else:
            logging.warn(json.dumps(user))

    # iterate through the user ids and write them to stdout
    for user_id in user_ids:
        print(str(user_id))


def load_config(filename, profile):
    if not os.path.isfile(filename):
        return None
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in ['access_token', 'access_token_secret',
                'consumer_key', 'consumer_secret']:
        try:
            data[key] = config.get(profile, key)
        except configparser.NoSectionError:
            sys.exit("no such profile %s in %s" % (profile, filename))
        except configparser.NoOptionError:
            sys.exit("missing %s from profile %s in %s" % (
                     key, profile, filename))
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
    Your friendly neighborhood Twitter archiving class. Twarc allows
    you to search for existing tweets, stream live tweets that match
    a filter query and lookup (hdyrate) a list of tweet ids.

    Each method search, stream and hydrate returns a tweet iterator which
    allows you to do what you want with the data. Twarc handles rate limiting
    in the API, so it will go to sleep when Twitter tells it to, and wake back
    up when it is able to get more data from the API.
    """

    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, connection_errors=0, http_errors=0):
        """
        Instantiate a Twarc instance. Make sure your environment variables
        are set.
        """

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.connection_errors = connection_errors
        self.http_errors = http_errors
        self.client = None
        self.last_response = None
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

    def user_lookup(self, screen_names=None, user_ids=None):
        """
        Returns fully-hydrated user objects for a list of up to 100
        screen_names or user_ids.  Provide screen_names or user_ids.
        """
        # Strip if any screen names are prefixed with '@'
        if screen_names:
            screen_names = [s.lstrip('@') for s in screen_names]
        ids = screen_names or user_ids
        id_type = "screen_name" if screen_names else "user_id"
        while ids:
            ids_str = ",".join(ids[:100])
            logging.info("Looking up users %s", ids_str)
            url = 'https://api.twitter.com/1.1/users/lookup.json'
            params = {id_type: ids_str}
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.info("no users matching %s", ids_str)
                    break
                raise e

            users = resp.json()
            for user in users:
                yield user

            ids = ids[100:]

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

if __name__ == "__main__":
    main()
