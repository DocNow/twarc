# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import types
import logging
import requests

import ssl
from requests.exceptions import ConnectionError
from requests.packages.urllib3.exceptions import ProtocolError

from .decorators import *
from requests_oauthlib import OAuth1, OAuth1Session


if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
    str_type = unicode
    import ConfigParser as configparser
    from urlparse import parse_qs
else:
    # Python 3
    get_input = input
    str_type = str
    import configparser
    from urllib.parse import parse_qs

log = logging.getLogger('twarc')


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
                 profile="", protected=False, tweet_mode="extended",
                 validate_keys=True):
        """
        Instantiate a Twarc instance. If keys aren't set we'll try to
        discover them in the environment or a supplied profile. If no
        profile is indicated the first section of the config files will
        be used.
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
        self.protected = protected

        if config:
            self.config = config
        else:
            self.config = self.default_config()

        self.get_keys()

        if validate_keys:
            self.validate_keys()

    @filter_protected
    def search(self, q, max_id=None, since_id=None, lang=None,
               result_type='recent', geocode=None, max_pages=None):
        """
        Pass in a query with optional max_id, min_id, lang or geocode
        and get back an iterator for decoded tweets. Defaults to recent (i.e.
        not mixed, the API default, or popular) tweets.
        """
        url = "https://api.twitter.com/1.1/search/tweets.json"
        params = {
            "count": 100,
            "q": q,
            "include_ext_alt_text": 'true'
        }
        if lang is not None:
            params['lang'] = lang
        if result_type in ['mixed', 'recent', 'popular']:
            params['result_type'] = result_type
        else:
            params['result_type'] = 'recent'
        if geocode is not None:
            params['geocode'] = geocode

        retrieved_pages = 0
        reached_end = False

        while True:
            if since_id:
                # Make the since_id inclusive, so we can avoid retrieving
                # an empty page of results in some cases
                params['since_id'] = str(int(since_id) - 1)
            if max_id:
                params['max_id'] = max_id

            resp = self.get(url, params=params)
            retrieved_pages += 1

            statuses = resp.json()["statuses"]

            if len(statuses) == 0:
                log.info("no new tweets matching %s", params)
                break

            for status in statuses:
                # We've certainly reached the end of new results
                if since_id is not None and status['id_str'] == str(since_id):
                    reached_end = True
                    break

                yield status

            if reached_end:
                log.info("no new tweets matching %s", params)
                break

            if max_pages is not None and retrieved_pages == max_pages:
                log.info("reached max page limit for %s", params)
                break

            max_id = str(int(status["id_str"]) - 1)

    def timeline(self, user_id=None, screen_name=None, max_id=None,
                 since_id=None, max_pages=None):
        """
        Returns a collection of the most recent tweets posted
        by the user indicated by the user_id or screen_name parameter.
        Provide a user_id or screen_name.
        """

        if user_id and screen_name:
            raise ValueError('only user_id or screen_name may be passed')

        # Strip if screen_name is prefixed with '@'
        if screen_name:
            screen_name = screen_name.lstrip('@')
        id = screen_name or str(user_id)
        id_type = "screen_name" if screen_name else "user_id"
        log.info("starting user timeline for user %s", id)

        if screen_name or user_id:
            url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        else:
            url = "https://api.twitter.com/1.1/statuses/home_timeline.json"

        params = {"count": 200, id_type: id, "include_ext_alt_text": "true"}

        retrieved_pages = 0
        reached_end = False

        while True:
            if since_id:
                # Make the since_id inclusive, so we can avoid retrieving
                # an empty page of results in some cases
                params['since_id'] = str(int(since_id) - 1)
            if max_id:
                params['max_id'] = max_id

            try:
                resp = self.get(url, params=params, allow_404=True)
                retrieved_pages += 1
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    log.warn("no timeline available for %s", id)
                    break
                elif e.response.status_code == 401:
                    log.warn("protected account %s", id)
                    break
                raise e

            statuses = resp.json()

            if len(statuses) == 0:
                log.info("no new tweets matching %s", params)
                break

            for status in statuses:
                # We've certainly reached the end of new results
                if since_id is not None and status['id_str'] == str(since_id):
                    reached_end = True
                    break
                # If you request an invalid user_id, you may still get
                # results so need to check.
                if not user_id or id == status.get("user",
                                                   {}).get("id_str"):
                    yield status

            if reached_end:
                log.info("no new tweets matching %s", params)
                break

            if max_pages is not None and retrieved_pages == max_pages:
                log.info("reached max page limit for %s", params)
                break

            max_id = str(int(status["id_str"]) - 1)

    def user_lookup(self, ids, id_type="user_id"):
        """
        A generator that returns users for supplied user ids, screen_names,
        or an iterator of user_ids of either. Use the id_type to indicate
        which you are supplying (user_id or screen_name)
        """

        if id_type not in ['user_id', 'screen_name']:
            raise RuntimeError("id_type must be user_id or screen_name")

        if not isinstance(ids, types.GeneratorType):
            ids = iter(ids)

        # TODO: this is similar to hydrate, maybe they could share code?

        lookup_ids = []

        def do_lookup():
            ids_str = ",".join(lookup_ids)
            log.info("looking up users %s", ids_str)
            url = 'https://api.twitter.com/1.1/users/lookup.json'
            params = {id_type: ids_str}
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    log.warning("no users matching %s", ids_str)
                raise e
            return resp.json()

        for id in ids:
            lookup_ids.append(id.strip())
            if len(lookup_ids) == 100:
                for u in do_lookup():
                    yield u
                lookup_ids = []

        if len(lookup_ids) > 0:
            for u in do_lookup():
                yield u

    def follower_ids(self, user, max_pages=None):
        """
        Returns Twitter user id lists for the specified user's followers.
        A user can be a specific using their screen_name or user_id
        """
        user = str(user)
        user = user.lstrip('@')
        url = 'https://api.twitter.com/1.1/followers/ids.json'

        if re.match(r'^\d+$', user):
            params = {'user_id': user, 'cursor': -1}
        else:
            params = {'screen_name': user, 'cursor': -1}

        retrieved_pages = 0

        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
                retrieved_pages += 1
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    log.info("no users matching %s", screen_name)
                raise e
            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield str_type(user_id)
            params['cursor'] = user_ids['next_cursor']
            
            if max_pages is not None and retrieved_pages == max_pages:
                log.info("reached max follower page limit for %s", params)
                break

    def friend_ids(self, user, max_pages=None):
        """
        Returns Twitter user id lists for the specified user's friend. A user
        can be specified using their screen_name or user_id.
        """
        user = str(user)
        user = user.lstrip('@')
        url = 'https://api.twitter.com/1.1/friends/ids.json'

        if re.match(r'^\d+$', user):
            params = {'user_id': user, 'cursor': -1}
        else:
            params = {'screen_name': user, 'cursor': -1}

        retrieved_pages = 0
        
        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
                retrieved_pages += 1
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    log.error("no users matching %s", user)
                raise e

            user_ids = resp.json()
            for user_id in user_ids['ids']:
                yield str_type(user_id)
            params['cursor'] = user_ids['next_cursor']

            if max_pages is not None and retrieved_pages == max_pages:
                log.info("reached max friend page limit for %s", params)
                break

    @filter_protected
    def filter(self, track=None, follow=None, locations=None, lang=[], 
               event=None, record_keepalive=False):
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
        params = {
            "stall_warning": True,
            "include_ext_alt_text": True
        }
        if track:
            params["track"] = track
        if follow:
            params["follow"] = follow
        if locations:
            params["locations"] = locations
        if lang:
            # should be a list, but just in case
            if isinstance(lang, list):
                params['language'] = ','.join(lang)
            else:
                params['language'] = lang
        headers = {'accept-encoding': 'deflate, gzip'}
        errors = 0
        while True:
            try:
                log.info("connecting to filter stream for %s", params)
                resp = self.post(url, params, headers=headers, stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=1024):
                    if event and event.is_set():
                        log.info("stopping filter")
                        # Explicitly close response
                        resp.close()
                        return
                    if not line:
                        log.info("keep-alive")
                        if record_keepalive:
                            yield "keep-alive"
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        log.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                log.error("caught http error %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    log.warning("too many errors")
                    raise e
                if e.response.status_code == 420:
                    if interruptible_sleep(errors * 60, event):
                        log.info("stopping filter")
                        return
                else:
                    if interruptible_sleep(errors * 5, event):
                        log.info("stopping filter")
                        return
            except Exception as e:
                errors += 1
                log.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    log.warning("too many exceptions")
                    raise e
                log.error(e)
                if interruptible_sleep(errors, event):
                    log.info("stopping filter")
                    return

    def sample(self, event=None, record_keepalive=False):
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
                log.info("connecting to sample stream")
                resp = self.post(url, params, headers=headers, stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=512):
                    if event and event.is_set():
                        log.info("stopping sample")
                        # Explicitly close response
                        resp.close()
                        return
                    if line == "":
                        log.info("keep-alive")
                        if record_keepalive:
                            yield "keep-alive"
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        log.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                log.error("caught http error %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    log.warning("too many errors")
                    raise e
                if e.response.status_code == 420:
                    if interruptible_sleep(errors * 60, event):
                        log.info("stopping filter")
                        return
                else:
                    if interruptible_sleep(errors * 5, event):
                        log.info("stopping filter")
                        return

            except Exception as e:
                errors += 1
                log.error("caught exception %s on %s try", e, errors)
                if self.http_errors and errors == self.http_errors:
                    log.warning("too many errors")
                    raise e
                if interruptible_sleep(errors, event):
                    log.info("stopping filter")
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
                log.error("uhoh: %s\n" % e)

    def hydrate(self, iterator):
        """
        Pass in an iterator of tweet ids and get back an iterator for the
        decoded JSON for each corresponding tweet.
        """
        ids = []
        url = "https://api.twitter.com/1.1/statuses/lookup.json"

        # lookup 100 tweets at a time
        for tweet_id in iterator:
            tweet_id = str(tweet_id)
            tweet_id = tweet_id.strip()  # remove new line if present
            ids.append(tweet_id)
            if len(ids) == 100:
                log.info("hydrating %s ids", len(ids))
                resp = self.post(url, data={
                    "id": ','.join(ids),
                    "include_ext_alt_text": 'true'
                })
                tweets = resp.json()
                tweets.sort(key=lambda t: t['id_str'])
                for tweet in tweets:
                    yield tweet
                ids = []

        # hydrate any remaining ones
        if len(ids) > 0:
            log.info("hydrating %s", ids)
            resp = self.post(url, data={
                "id": ','.join(ids),
                "include_ext_alt_text": 'true'
            })
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
        log.info("retrieving retweets of %s", tweet_id)
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
                log.info("no region matching WOEID %s", woeid)
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
        log.info("looking for replies to: %s", tweet_id)
        for reply in self.search("to:%s" % screen_name, since_id=tweet_id):

            if reply['in_reply_to_status_id_str'] != tweet_id:
                continue

            if reply['id_str'] in prune:
                log.info("ignoring pruned tweet id %s", reply['id_str'])
                continue

            log.info("found reply: %s", reply["id_str"])

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
        log.info("prune=%s", prune)
        if recursive and reply_to_id and reply_to_id not in prune:
            t = self.tweet(reply_to_id)
            if t:
                log.info("found reply-to: %s", t['id_str'])
                prune = prune + (tweet['id_str'],)
                for r in self.replies(t, recursive=True, prune=prune):
                    yield r

        # if this tweet is a quote go get that too whatever tweets it
        # may be in reply to

        quote_id = tweet.get('quoted_status_id_str')
        if recursive and quote_id and quote_id not in prune:
            t = self.tweet(quote_id)
            if t:
                log.info("found quote: %s", t['id_str'])
                prune = prune + (tweet['id_str'],)
                for r in self.replies(t, recursive=True, prune=prune):
                    yield r

    def list_members(self, list_id=None, slug=None, owner_screen_name=None, owner_id=None):
        """
        Returns the members of a list.

        List id or (slug and (owner_screen_name or owner_id)) are required
        """
        assert list_id or (slug and (owner_screen_name or owner_id))
        url = 'https://api.twitter.com/1.1/lists/members.json'
        params = {'cursor': -1}
        if list_id:
            params['list_id'] = list_id
        else:
            params['slug'] = slug
            if owner_screen_name:
                params['owner_screen_name'] = owner_screen_name
            else:
                params['owner_id'] = owner_id

        while params['cursor'] != 0:
            try:
                resp = self.get(url, params=params, allow_404=True)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    log.error("no matching list")
                raise e

            users = resp.json()
            for user in users['users']:
                yield user
            params['cursor'] = users['next_cursor']

    def oembed(self, tweet_url, **params):
        """
        Returns the oEmbed JSON for a tweet. The JSON includes an html
        key that contains the HTML for the embed. You can pass in 
        parameters that correspond to the paramters that Twitter's
        statuses/oembed endpoint supports. For example:

        o = client.oembed('https://twitter.com/biz/status/21', theme='dark')
        """
        log.info("generating embedding for tweet %s", tweet_url)
        url = "https://publish.twitter.com/oembed"

        params['url'] = tweet_url
        resp = self.get(url, params=params)

        return resp.json()

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
            kwargs["params"] = {"tweet_mode": self.tweet_mode}

        # Pass allow 404 to not retry on 404
        allow_404 = kwargs.pop('allow_404', False)
        connection_error_count = kwargs.pop('connection_error_count', 0)
        try:
            log.info("getting %s %s", args, kwargs)
            r = self.last_response = self.client.get(*args, timeout=(3.05, 31),
                                                     **kwargs)
            # this has been noticed, believe it or not
            # https://github.com/edsu/twarc/issues/75
            if r.status_code == 404 and not allow_404:
                log.warning("404 from Twitter API! trying again")
                time.sleep(1)
                r = self.get(*args, **kwargs)
            return r
        except (ssl.SSLError, ConnectionError, ProtocolError) as e:
            connection_error_count += 1
            log.error("caught connection error %s on %s try", e,
                          connection_error_count)
            if (self.connection_errors and
                    connection_error_count == self.connection_errors):
                log.error("received too many connection errors")
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
            log.info("posting %s %s", args, kwargs)
            self.last_response = self.client.post(*args, timeout=(3.05, 31),
                                                  **kwargs)
            return self.last_response
        except (ssl.SSLError, ConnectionError, ProtocolError) as e:
            connection_error_count += 1
            log.error("caught connection error %s on %s try", e,
                          connection_error_count)
            if (self.connection_errors and
                    connection_error_count == self.connection_errors):
                log.error("received too many connection errors")
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
            raise RuntimeError("MissingKeys")

        if self.client:
            log.info("closing existing http session")
            self.client.close()
        if self.last_response:
            log.info("closing last response")
            self.last_response.close()
        log.info("creating http session")

        self.client = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )

    def get_keys(self):
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

    def validate_keys(self):
        """
        Validate the keys provided are authentic credentials.
        """
        url = 'https://api.twitter.com/1.1/account/verify_credentials.json'

        keys_present = self.consumer_key and self.consumer_secret and \
                       self.access_token and self.access_token_secret

        if keys_present:
            try:
                # Need to explicitly reconnect to confirm the current creds
                # are used in the session object.
                self.connect()
                self.get(url)
            except requests.HTTPError as e:
                if e.response.status_code == 401:
                    raise RuntimeError('Invalid credentials provided.')
                else:
                    raise e
        else:
            raise RuntimeError('Incomplete credentials provided.')

    def load_config(self):
        path = self.config
        profile = self.profile
        log.info("loading %s profile from config %s", profile, path)

        if not path or not os.path.isfile(path):
            return {}

        config = configparser.ConfigParser()
        config.read(self.config)

        if len(config.sections()) >= 1 and not profile:
            profile = config.sections()[0]

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

    def save_config(self, profile):
        if not self.config:
            return
        config = configparser.ConfigParser()
        config.read(self.config)

        if config.has_section(profile):
            config.remove_section(profile)

        config.add_section(profile)
        config.set(profile, 'consumer_key', self.consumer_key)
        config.set(profile, 'consumer_secret', self.consumer_secret)
        config.set(profile, 'access_token', self.access_token)
        config.set(profile, 'access_token_secret',
                   self.access_token_secret)
        with open(self.config, 'w') as config_file:
            config.write(config_file)

        return config

    def configure(self):
        print("\nTwarc needs to know a few things before it can talk to Twitter on your behalf.\n")

        reuse = False
        if self.consumer_key and self.consumer_secret:
            print("You already have these application keys in your config %s\n" % self.config)
            print("consumer key: %s" % self.consumer_key)
            print("consumer secret: %s" % self.consumer_secret)
            reuse = get_input("\nWould you like to use those for your new profile? [y/n] ")
            reuse = reuse.lower() == 'y'

        if not reuse:
            print("\nPlease enter your Twitter application credentials from apps.twitter.com:\n")

            self.consumer_key = get_input('consumer key: ')
            self.consumer_secret = get_input('consumer secret: ')

        request_token_url = 'https://api.twitter.com/oauth/request_token'
        oauth = OAuth1(self.consumer_key, client_secret=self.consumer_secret)
        r = requests.post(url=request_token_url, auth=oauth)

        credentials = parse_qs(r.text)
        if not credentials:
            print("\nError: invalid credentials.")
            print("Please check that you are copying and pasting correctly and try again.\n")
            return

        resource_owner_key = credentials.get('oauth_token')[0]
        resource_owner_secret = credentials.get('oauth_token_secret')[0]

        base_authorization_url = 'https://api.twitter.com/oauth/authorize'
        authorize_url = base_authorization_url + '?oauth_token=' + resource_owner_key
        print('\nPlease log into Twitter and visit this URL in your browser:\n%s' % authorize_url)
        verifier = get_input('\nAfter you have authorized the application please enter the displayed PIN: ')

        access_token_url = 'https://api.twitter.com/oauth/access_token'
        oauth = OAuth1(self.consumer_key,
                       client_secret=self.consumer_secret,
                       resource_owner_key=resource_owner_key,
                       resource_owner_secret=resource_owner_secret,
                       verifier=verifier)
        r = requests.post(url=access_token_url, auth=oauth)
        credentials = parse_qs(r.text)

        if not credentials:
            print('\nError: invalid PIN')
            print('Please check that you entered the PIN correctly and try again.\n')
            return

        self.access_token = resource_owner_key = credentials.get('oauth_token')[0]
        self.access_token_secret = credentials.get('oauth_token_secret')[0]

        screen_name = credentials.get('screen_name')[0]

        config = self.save_config(screen_name)
        print('\nThe credentials for %s have been saved to your configuration file at %s' % (screen_name, self.config))
        print('\n✨ ✨ ✨  Happy twarcing! ✨ ✨ ✨\n')

        if len(config.sections()) > 1:
            print('Note: you have multiple profiles in %s so in order to use %s you will use --profile\n' % (self.config, screen_name))

    def default_config(self):
        return os.path.join(os.path.expanduser("~"), ".twarc")


