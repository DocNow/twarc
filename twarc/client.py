import os
import re
import sys
import json
import logging
import requests

from .decorators import *
from requests_oauthlib import OAuth1Session


if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
    str_type = unicode
    import ConfigParser as configparser
else:
    # Python 3
    get_input = input
    str_type = str
    import configparser


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
                 profile="main", tweet_mode="extended"):
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
        self.profile = profile
        self.client = None
        self.last_response = None
        self.tweet_mode = tweet_mode

        if config:
            self.config = config
        else:
            self.config = self.default_config()

        self.check_keys()

    def search(self, q, max_id=None, since_id=None, lang=None,
               result_type='recent', geocode=None):
        """
        Pass in a query with optional max_id, min_id, lang or geocode
        and get back an iterator for decoded tweets. Defaults to recent (i.e.
        not mixed, the API default, or popular) tweets.
        """
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
            lookup_ids.append(id.strip())
            if len(lookup_ids) == 100:
                for u in do_lookup():
                    yield u
                lookup_ids = []

        if len(lookup_ids) > 0:
            for u in do_lookup():
                yield u

    def follower_ids(self, user):
        """
        Returns Twitter user id lists for the specified user's followers. 
        A user can be a specific using their screen_name or user_id
        """
        user = str(user)
        user = user.lstrip('@')
        url = 'https://api.twitter.com/1.1/followers/ids.json'

        if re.match('^\d+$', user):
            params = {'user_id': user, 'cursor': -1}
        else:
            params = {'screen_name': user, 'cursor': -1}

        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.info("no users matching %s", screen_name)
                raise e
            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield str_type(user_id)
            params['cursor'] = user_ids['next_cursor']

    def friend_ids(self, user):
        """
        Returns Twitter user id lists for the specified user's friend. A user
        can be specified using their screen_name or user_id.
        """
        user = str(user)
        user = user.lstrip('@')
        url = 'https://api.twitter.com/1.1/friends/ids.json'

        if re.match('^\d+$', user):
            params = {'user_id': user, 'cursor': -1}
        else:
            params = {'screen_name': user, 'cursor': -1}

        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logging.error("no users matching %s", user)
                raise e

            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield str_type(user_id)
            params['cursor'] = user_ids['next_cursor']

    def filter(self, track=None, follow=None, locations=None, event=None):
        """
        Returns an iterator for tweets that match a given filter track from
        the livestream of tweets happening right now.

        If a threading.Event is provided for event and the event is set,
        the filter will be interrupted.
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
                    if event and event.is_set():
                        logging.info("stopping filter")
                        # Explicitly close response
                        resp.close()
                        return
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
                    if interruptible_sleep(errors * 60, event):
                        logging.info("stopping filter")
                        return
                else:
                    if interruptible_sleep(errors * 5, event):
                        logging.info("stopping filter")
                        return
            except Exception as e:
                errors += 1
                logging.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many exceptions")
                    raise e
                logging.error(e)
                if interruptible_sleep(errors, event):
                    logging.info("stopping filter")
                    return

    def sample(self, event=None):
        """
        Returns a small random sample of all public statuses. The Tweets
        returned by the default access level are the same, so if two different
        clients connect to this endpoint, they will see the same Tweets.

        If a threading.Event is provided for event and the event is set,
        the sample will be interrupted.
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
                    if event and event.is_set():
                        logging.info("stopping sample")
                        # Explicitly close response
                        resp.close()
                        return
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
                    if interruptible_sleep(errors * 60, event):
                        logging.info("stopping filter")
                        return
                else:
                    if interruptible_sleep(errors * 5, event):
                        logging.info("stopping filter")
                        return

            except Exception as e:
                errors += 1
                logging.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    logging.warn("too many errors")
                    raise e
                if interruptible_sleep(errors, event):
                    logging.info("stopping filter")
                    return

    def dehydrate(self, iterator):
        """
        Pass in an iterator of tweets' JSON and get back an iterator of the
        IDs of each tweet.
        """
        for line in iterator:
            try:
                yield json.loads(line)['id_str']
            except Exception as e:
                logging.error("uhoh: %s\n" % e)

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
            resp = self.post(url, data={"id": ','.join(ids)})
            for tweet in resp.json():
                yield tweet

    def tweet(self, tweet_id):
        try:
            return next(self.hydrate([tweet_id]))
        except StopIteration:
            return []

    def retweets(self, tweet_id):
        """
        Retrieves up to the last 100 retweets for the provided
        tweet.
        """
        logging.info("retrieving retweets of %s", tweet_id)
        url = "https://api.twitter.com/1.1/statuses/retweets/""{}.json".format(
                tweet_id)

        resp = self.get(url, params={"count": 100})
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

    def replies(self, tweet, recursive=False, prune=()):
        """
        replies returns a generator of tweets that are replies for a given 
        tweet. It includes the original tweet. If you would like to fetch the
        replies to the replies use recursive=True which will do a depth-first
        recursive walk of the replies. It also walk up the reply chain if you
        supply a tweet that is itself a reply to another tweet. You can
        optionally supply a tuple of tweet ids to ignore during this traversal 
        using the prune parameter.
        """

        yield tweet

        # get replies to the tweet
        screen_name = tweet['user']['screen_name']
        tweet_id = tweet['id_str']
        logging.info("looking for replies to: %s", tweet_id)
        for reply in self.search("to:%s" % screen_name, since_id=tweet_id):

            if reply['in_reply_to_status_id_str'] != tweet_id:
                continue

            if reply['id_str'] in prune:
                logging.info("ignoring pruned tweet id %s", reply['id_str'])
                continue

            logging.info("found reply: %s", reply["id_str"])

            if recursive:
                if reply['id_str'] not in prune:
                    prune = prune + (tweet_id,)
                    for r in self.replies(reply, recursive, prune):
                        yield r
            else:
                yield reply

        # if this tweet is itself a reply to another tweet get it and 
        # get other potential replies to it

        reply_to_id = tweet.get('in_reply_to_status_id_str')
        logging.info("prune=%s", prune)
        if recursive and reply_to_id and reply_to_id not in prune:
            t = self.tweet(reply_to_id)
            if t:
                logging.info("found reply-to: %s", t['id_str'])
                prune = prune + (tweet['id_str'],)
                for r in self.replies(t, recursive=True, prune=prune):
                    yield r

        # if this tweet is a quote go get that too whatever tweets it
        # may be in reply to

        quote_id = tweet.get('quotes_status_id_str')
        if recursive and quote_id and quote_id not in prune:
            t = self.tweet(quote_id)
            if t:
                logging.info("found quote: %s", t['id_str'])
                prune = prune + (tweet['id_str'],)
                for r in self.replies(t, recursive=True, prune=prune):
                    yield r

    @rate_limit
    @catch_conn_reset
    @catch_timeout
    @catch_gzip_errors
    def get(self, *args, **kwargs):
        if not self.client:
            self.connect()

        if "params" in kwargs:
            kwargs["params"]["tweet_mode"] = self.tweet_mode
        else:
            kwargs["params"] = {"tweet_node": self.tweet_mode}

        # Pass allow 404 to not retry on 404
        allow_404 = kwargs.pop('allow_404', False)
        connection_error_count = kwargs.pop('connection_error_count', 0)
        try:
            logging.info("getting %s %s", args, kwargs)
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
            logging.error("caught connection error %s on %s try", e,
                          connection_error_count)
            if (self.connection_errors and
                    connection_error_count == self.connection_errors):
                logging.error("received too many connection errors")
                raise e
            else:
                self.connect()
                kwargs['connection_error_count'] = connection_error_count
                kwargs['allow_404'] = allow_404
                return self.get(*args, **kwargs)

    @rate_limit
    @catch_conn_reset
    @catch_timeout
    @catch_gzip_errors
    def post(self, *args, **kwargs):
        if not self.client:
            self.connect()

        if "data" in kwargs:
            kwargs["data"]["tweet_mode"] = self.tweet_mode

        connection_error_count = kwargs.pop('connection_error_count', 0)
        try:
            logging.info("posting %s %s", args, kwargs)
            self.last_response = self.client.post(*args, **kwargs)
            return self.last_response
        except requests.exceptions.ConnectionError as e:
            connection_error_count += 1
            logging.error("caught connection error %s on %s try", e,
                          connection_error_count)
            if (self.connection_errors and
                    connection_error_count == self.connection_errors):
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
        if not (self.consumer_key and self.consumer_secret and self.access_token
                and self.access_token_secret):
            raise MissingKeys()

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
        environment, config file. Return True if all the keys were found
        and False if not.
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

        if self.config and not (self.consumer_key and
                                self.consumer_secret and
                                self.access_token and
                                self.access_token_secret):
            self.load_config()

        return self.consumer_key and self.consumer_secret and \
               self.access_token and self.access_token_secret

    def load_config(self):
        path = self.config
        profile = self.profile
        logging.info("loading %s profile from config %s", profile, path)

        if not path or not os.path.isfile(path):
            return {}
        
        config = configparser.ConfigParser()
        config.read(self.config)
        data = {}
        for key in ['access_token', 'access_token_secret',
                    'consumer_key', 'consumer_secret']:
            try:
                setattr(self, key, config.get(profile, key))
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
        print("\nPlease enter Twitter authentication credentials.\n")

        def i(name):
            return get_input(name.replace('_', ' ') + ": ")

        self.consumer_key = i('consumer_key')
        self.consumer_secret = i('consumer_secret')
        self.access_token = i('access_token')
        self.access_token_secret = i('access_token_secret')
        self.save_config()

    def default_config(self):
        return os.path.join(os.path.expanduser("~"), ".twarc")


