# -*- coding: utf-8 -*-

"""
Support for the Twitter v2 API.
"""

import ssl
import json
import logging
import datetime
import requests

from twarc import expansions
from twarc.decorators import *
from requests.exceptions import ConnectionError
from requests.packages.urllib3.exceptions import ProtocolError

log = logging.getLogger("twarc")


class Twarc2:
    """
    A client for the Twitter v2 API.
    """

    def __init__(
        self,
        bearer_token,
        connection_errors=0,
        http_errors=0,
    ):
        """
        Instantiate a Twarc2 instance to talk to the Twitter V2+ API.

        Currently only bearer_token authentication is supported (ie, only
        Oauth2.0 app authentication). You can retrieve your bearer_token from
        the Twitter developer dashboard for your project.

        Unlike the original Twarc client, this object does not perform any
        configuration directly.

        TODO: Figure out how to handle the combinations of:

        - bearer_token
        - api_key and api_secret (which can be used to retrieve a bearer token)
        - access_token and access_token_secret (used with the api_key/secret for
          user authentication/OAuth 1.0a)

        Arguments:

        - bearer_token: the Twitter API bearer_token for autghe
        """
        self.api_version = "2"
        self.bearer_token = bearer_token
        self.connection_errors = connection_errors
        self.http_errors = http_errors

        self.client = None
        self.last_response = None

        self.connect()

    def search_recent(self, query, since_id=None, until_id=None,
            start_time=None, end_time=None):
        """
        Search Twitter for the given query, using the /search/recent endpoint.

        Approximately the last seven days are indexed by Twitter - if you want
        to search the full archive you can use the `full_archive_search` method,
        but note the need for an elevated access level.

        query: The query string to be passed directly to the Twitter API.
        since_id: Return all tweets since this tweet_id.
        until_id: Return all tweets up to this tweet_id.
        start_time: Return all tweets after this time (UTC datetime).
        end_time: Return all tweets before this time (UTC datetime).
        """

        url = "https://api.twitter.com/2/tweets/search/recent"

        params = expansions.EVERYTHING.copy()
        params["max_results"] = 100
        params["query"] = query

        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if start_time:
            params["start_time"] = _ts(start_time)
        if end_time:
            params["end_time"] = _ts(end_time)

        for response in self.get_paginated(url, params=params):
            # can return without 'data' if there are no results
            if 'data' in response:
                yield response

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

            return resp.json()

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
            return resp.json()

        batch = []
        for item in users:
            batch.append(str(item).strip())
            if len(batch) == 100:
                yield lookup_batch(batch)
                batch = []

        if batch:
            yield (lookup_batch(batch))

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
                        yield json.loads(line.decode())

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

    def add_stream_rules(self, rules):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.post(url, {"add": rules}).json()

    def get_stream_rules(self):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.get(url).json()

    def delete_stream_rule_ids(self, rule_ids):
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        return self.post(url, {"delete": {"ids": rule_ids}}).json()

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

            if line == b'' and record_keep_alives:
                log.info('keep-alive')
                yield "keep-alive"
            else:
                yield json.loads(line.decode())


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

        page = self.get(*args, **kwargs).json()

        yield page

        while "next_token" in page["meta"]:
            if "params" in kwargs:
                kwargs["params"]["next_token"] = page["meta"]["next_token"]
            else:
                kwargs["params"] = {"next_token": page["meta"]["next_token"]}

            page = self.get(*args, **kwargs).json()
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

        if self.client:
            log.info("closing existing http session")
            self.client.close()

        if self.last_response:
            log.info("closing last response")
            self.last_response.close()

        log.info("creating http session")

        client = requests.Session()

        # For bearer token authentication we only need to setup this header - no
        # OAuth 1.0a dance required. This will likely become more complex when
        # we consider user auth rather than just application authentication.
        client.headers.update({"Authorization": f"Bearer {self.bearer_token}"})

        self.client = client

def _ts(dt):
    """
    Return ISO 8601 / RFC 3339 datetime in UTC. If no timezone is specified it
    is assumed to be in UTC. The Twitter API does not resolve accept
    microseconds.
    """
    if dt.tzinfo:
        dt = dt.astimezone(datetime.timezone.utc)
    else:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat(timespec='seconds')


_r = []