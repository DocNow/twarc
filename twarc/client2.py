# -*- coding: utf-8 -*-

"""
Support for the Twitter v2 API.
"""

import re
import ssl
import json
import logging
import requests
import datetime

from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import ConnectionError
from requests.packages.urllib3.exceptions import ProtocolError
from requests_oauthlib import OAuth1Session, OAuth2Session

from twarc import expansions
from twarc.decorators import *
from twarc.version import version


log = logging.getLogger("twarc")


class Twarc2:
    """
    A client for the Twitter v2 API.
    """

    def __init__(
        self,
        consumer_key=None,
        consumer_secret=None,
        access_token=None,
        access_token_secret=None,
        bearer_token=None,
        connection_errors=0,
        http_errors=0,
        metadata=True,
    ):
        """
        Instantiate a Twarc2 instance to talk to the Twitter V2+ API.

        The client can use either App or User authentication, but only one at a
        time. Whether app auth or user auth is used depends on which credentials
        are provided on initialisation:

        1. If a `bearer_token` is passed, app auth is always used.
        2. If a `consumer_key` and `consumer_secret` are passed without an
           `access_token` and `access_token_secret`, app auth is used.
        3. If `consumer_key`, `consumer_secret`, `access_token` and
           `access_token_secret` are all passed, then user authentication
           is used instead.

        """
        self.api_version = "2"
        self.connection_errors = connection_errors
        self.http_errors = http_errors
        self.metadata = metadata
        self.bearer_token = None

        if bearer_token:
            self.bearer_token = bearer_token
            self.auth_type = "application"

        elif (consumer_key and consumer_secret):
            if access_token and access_token_secret:
                self.consumer_key = consumer_key
                self.consumer_secret = consumer_secret
                self.access_token = access_token
                self.access_token_secret = access_token_secret
                self.auth_type = "user"

            else:
                self.consumer_key = consumer_key
                self.consumer_secret = consumer_secret
                self.auth_type = "application"

        else:
            raise ValueError(
                "Must pass either a bearer_token or consumer/access_token keys and secrets"
            )

        self.client = None
        self.last_response = None

        self.connect()

    def _search(
        self, url, query, since_id, until_id, start_time, end_time, max_results
    ):

        params = expansions.EVERYTHING.copy()
        params['max_results'] = max_results
        params["query"] = query

        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if start_time:
            params["start_time"] = _ts(start_time)
        if end_time:
            params["end_time"] = _ts(end_time)

        count = 0
        for response in self.get_paginated(url, params=params):
            # can return without 'data' if there are no results
            if 'data' in response:
                count += len(response['data'])
                yield response
            else:
                log.info(f'no more results for search')

    def search_recent(
            self, query, since_id=None, until_id=None, start_time=None,
            end_time=None, max_results=100
        ):
        """
        Search Twitter for the given query in the last seven days, using the
        /search/recent endpoint.

        query: The query string to be passed directly to the Twitter API.
        since_id: Return all tweets since this tweet_id.
        until_id: Return all tweets up to this tweet_id.
        start_time: Return all tweets after this time (UTC datetime).
        end_time: Return all tweets before this time (UTC datetime).
        max_results: The maximum number of results per request. Max is 100 or
                     for recent search.
        """
        url = "https://api.twitter.com/2/tweets/search/recent"
        return self._search(
            url, query, since_id, until_id, start_time, end_time, max_results
        )

    @requires_app_auth
    def search_all(
        self, query, since_id=None, until_id=None, start_time=None,
        end_time=None, max_results=500
    ):
        url = "https://api.twitter.com/2/tweets/search/all"
        return self._search(
            url, query, since_id, until_id, start_time, end_time, max_results
        )

    def tweet_lookup(self, tweet_ids):
        """
        Lookup tweets, taking an iterator of IDs and returning pages of fully
        expanded tweet objects.

        This can be used to rehydrate a collection shared as only tweet IDs.

        Yields one page of tweets at a time, in blocks of up to 100.
        """

        def lookup_batch(tweet_id):

            url = "https://api.twitter.com/2/tweets"

            params = expansions.EVERYTHING.copy()
            params["ids"] = ",".join(tweet_id)

            resp = self.get(url, params=params)
            data = resp.json()

            if self.metadata:
                data = _append_metadata(data, resp.url)

            return data

        tweet_id_batch = []

        for tweet_id in tweet_ids:
            tweet_id_batch.append(str(int(tweet_id)))

            if len(tweet_id_batch) == 100:
                yield lookup_batch(tweet_id_batch)
                tweet_id_batch = []

        if tweet_id_batch:
            yield (lookup_batch(tweet_id_batch))

    def user_lookup(self, users, usernames=False):
        """
        Returns fully populated user profiles for the given iterator of
        user_id or usernames. By default user_lookup expects user ids but if
        you want to pass in usernames set usernames = True.

        Yields one page of results at a time (in blocks of at most 100 user
        profiles).
        """

        if usernames:
            url = "https://api.twitter.com/2/users/by"
        else:
            url = "https://api.twitter.com/2/users"

        def lookup_batch(users):
            params = expansions.USER_EVERYTHING.copy()
            if usernames:
                params["usernames"] = ",".join(users)
            else:
                params["ids"] = ",".join(users)

            resp = self.get(url, params=params)
            data = resp.json()

            if self.metadata:
                data = _append_metadata(data, resp.url)

            return data

        batch = []
        for item in users:
            batch.append(str(item).strip())
            if len(batch) == 100:
                yield lookup_batch(batch)
                batch = []

        if batch:
            yield (lookup_batch(batch))

    @requires_app_auth
    def sample(self, event=None, record_keepalive=False):
        """
        Returns a sample of all publically posted tweets.

        The sample is based on slices of each second, not truely randomised. The
        same tweets are returned for all users of this endpoint.

        If a threading.Event is provided for event and the event is set, the
        sample will be interrupted. This can be used for coordination with other
        programs.
        """
        url = "https://api.twitter.com/2/tweets/sample/stream"
        errors = 0

        while True:
            try:
                log.info("Connecting to V2 sample stream")
                resp = self.get(url, params=expansions.EVERYTHING.copy(), stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=512):

                    # quit & close the stream if the event is set
                    if event and event.is_set():
                        log.info("stopping sample")
                        resp.close()
                        return

                    # return the JSON data w/ optional keep-alive
                    if not line:
                        log.info("keep-alive")
                        if record_keepalive:
                            yield "keep-alive"
                        continue
                    else:
                        data = json.loads(line.decode())
                        if self.metadata:
                            data = _append_metadata(data, resp.url)
                        yield data

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
    @requires_app_auth
    def add_stream_rules(self, rules):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.post(url, {"add": rules}).json()

    @requires_app_auth
    def get_stream_rules(self):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.get(url).json()

    @requires_app_auth
    def delete_stream_rule_ids(self, rule_ids):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.post(url, {"delete": {"ids": rule_ids}}).json()

    @requires_app_auth
    def stream(self, event=None, record_keep_alives=False):
        url = "https://api.twitter.com/2/tweets/search/stream"
        params = expansions.EVERYTHING.copy()
        resp = self.get(url, params=params, stream=True)
        for line in resp.iter_lines():

            # quit & close the stream if the event is set
            if event and event.is_set():
                log.info('stopping filter')
                resp.close()
                return

            if line == b'':
                log.info('keep-alive')
                if record_keep_alives:
                    yield "keep-alive"
            else:
                data = json.loads(line.decode())
                if self.metadata:
                    data = _append_metadata(data, resp.url)

                yield data

    def _timeline(
        self, user_id, timeline_type, since_id, until_id, start_time, end_time
    ):
        """Helper function for user and mention timelines"""

        url = f"https://api.twitter.com/2/users/{user_id}/{timeline_type}"

        params = expansions.EVERYTHING.copy()
        params["max_results"] = 100

        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if start_time:
            params["start_time"] = _ts(start_time)
        if end_time:
            params["end_time"] = _ts(end_time)

        count = 0
        for response in self.get_paginated(url, params=params):
            # can return without 'data' if there are no results
            if 'data' in response:
                count += len(response['data'])
                yield response
            else:
                log.info(f'no more results for timeline')

    def timeline(
        self, user, since_id=None, until_id=None, start_time=None,
        end_time=None
    ):
        """Retrieve up to the 3200 most recent tweets made by the given user."""
        user_id = self._ensure_user_id(user)
        return self._timeline(
            user_id, 'tweets', since_id, until_id, start_time, end_time
        )

    def mentions(
        self, user, since_id=None, until_id=None, start_time=None,
        end_time=None
    ):
        """
        Retrieve up to the 800 most recent tweets mentioning the given user.

        """
        user_id = self._ensure_user_id(user)
        return self._timeline(
            user_id, 'mentions', since_id, until_id, start_time, end_time
        )

    def following(self, user):
        """
        Retrieve the user profiles of accounts followed by the given user.

        """
        user_id = self._ensure_user_id(user)
        params = expansions.USER_EVERYTHING.copy()
        params["max_results"] = 1000
        url = f"https://api.twitter.com/2/users/{user_id}/following"
        return self.get_paginated(url, params=params)

    def followers(self, user):
        """
        Retrieve the user profiles of accounts following the given user.

        """
        user_id = self._ensure_user_id(user)
        params = expansions.USER_EVERYTHING.copy()
        params["max_results"] = 1000
        url = f"https://api.twitter.com/2/users/{user_id}/followers"
        return self.get_paginated(url, params=params)

    @rate_limit
    @catch_conn_reset
    @catch_timeout
    @catch_gzip_errors
    def get(self, *args, **kwargs):

        # Pass allow 404 to not retry on 404
        allow_404 = kwargs.pop("allow_404", False)
        connection_error_count = kwargs.pop("connection_error_count", 0)
        try:
            log.info("getting %s %s", args, kwargs)
            r = self.last_response = self.client.get(
                *args, timeout=(3.05, 31), **kwargs
            )
            # this has been noticed, believe it or not
            # https://github.com/edsu/twarc/issues/75
            if r.status_code == 404 and not allow_404:
                log.warning("404 from Twitter API! trying again")
                time.sleep(1)
                r = self.get(*args, **kwargs)
            return r
        except (ssl.SSLError, ConnectionError, ProtocolError) as e:
            connection_error_count += 1
            log.error("caught connection error %s on %s try", e, connection_error_count)
            if (
                self.connection_errors
                and connection_error_count == self.connection_errors
            ):
                log.error("received too many connection errors")
                raise e
            else:
                self.connect()
                kwargs["connection_error_count"] = connection_error_count
                kwargs["allow_404"] = allow_404
                return self.get(*args, **kwargs)

    def get_paginated(self, *args, **kwargs):
        """
        A wrapper around the `get` method that handles Twitter token based
        pagination.

        Yields one page (one API response) at a time.
        """

        resp = self.get(*args, **kwargs)
        page = resp.json()

        url = args[0]
        
        if self.metadata:
            page = _append_metadata(page, resp.url)

        yield page

        endings = ['mentions', 'tweets', 'following', 'followers']

        # The search endpoints only take a next_token, but the timeline
        # endpoints take a pagination_token instead - this is a bit of a hack,
        # but check the URL ending to see which we should use.
        if any(url.endswith(end) for end in endings):
            token_param = "pagination_token"
        else:
            token_param = "next_token"

        while "next_token" in page["meta"]:
            if "params" in kwargs:
                kwargs["params"][token_param] = page["meta"]["next_token"]
            else:
                kwargs["params"] = {token_param: page["meta"]["next_token"]}

            resp = self.get(*args, **kwargs)
            page = resp.json()

            if self.metadata:
                page = _append_metadata(page, resp.url)

            yield page

    @rate_limit
    def post(self, url, json_data):
        if not self.client:
            self.connect()
        return self.client.post(url, json=json_data)

    def connect(self):
        """
        Sets up the HTTP session to talk to Twitter. If one is active it is
        closed and another one is opened.
        """
        if self.last_response:
            self.last_response.close()

        if self.client:
            self.client.close()

        if self.auth_type == "application" and self.bearer_token:
            log.info('Creating HTTP session headers for app auth.')
            self.client = requests.Session()
            self.client.headers.update(
                {"Authorization": f"Bearer {self.bearer_token}"}
            )
        elif self.auth_type == "application":
            log.info('Creating app auth client via OAuth2')
            client = BackendApplicationClient(client_id=self.consumer_key)
            self.client = OAuth2Session(client=client)
            self.client.fetch_token(
                token_url='https://api.twitter.com/oauth2/token',
                client_id=self.consumer_key,
                client_secret=self.consumer_secret
            )
        else:
            log.info('creating user auth client')
            self.client = OAuth1Session(
                client_key=self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret
            )

    def _ensure_user_id(self, user):
        user = str(user)
        if re.match(r'^\d+$', user):
            return user
        else:
            results = next(self.user_lookup([user], usernames=True))
            if 'data' in results and len(results['data']) > 0:
                return results['data'][0]['id']
            else:
                raise ValueError(f"No such user {user}")

def _ts(dt):
    """
    Return ISO 8601 / RFC 3339 datetime in UTC. If no timezone is specified it
    is assumed to be in UTC. The Twitter API does not accept microseconds.
    """
    if dt.tzinfo:
        dt = dt.astimezone(datetime.timezone.utc)
    else:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat(timespec='seconds')

def _utcnow():
    """Return _now_ in ISO 8601 / RFC 3339 datetime in UTC."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec='seconds'
    )

def _append_metadata(result, url):
    result["__twarc"] = {
                    "url": url,
                    "version": version,
                    "retrieved_at": _utcnow()
                }
    return result
