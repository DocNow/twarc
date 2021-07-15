import os
import time
import click
import logging
import requests

import datetime
import humanize
from tqdm.auto import tqdm
from functools import wraps


log = logging.getLogger("twarc")


def rate_limit(f, tries=30):
    """
    A decorator to handle rate limiting from the Twitter v2 API. If
    a rate limit error is encountered we will sleep until we can
    issue the API call again.
    """

    @wraps(f)
    def new_f(*args, **kwargs):
        errors = 0
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code in [200, 201]:
                errors = 0
                return resp
            elif resp.status_code == 429:
                reset = int(resp.headers["x-rate-limit-reset"])
                now = time.time()
                seconds = reset - now + 10
                if seconds < 1:
                    seconds = 10
                log.warning("rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            elif resp.status_code >= 500:
                errors += 1
                if errors > tries:
                    log.warning(f"too many errors ({tries}) from Twitter, giving up")
                    resp.raise_for_status()
                seconds = errors ** 2
                log.warning(
                    "caught %s from Twitter API, sleeping %s", resp.status_code, seconds
                )
                time.sleep(seconds)
            else:
                log.error("Unexpected HTTP response: %s", resp)
                resp.raise_for_status()

    return new_f


def catch_request_exceptions(f, tries=30):
    """
    A decorator to handle all request exceptions. This decorator will catch
    *any* request level error, reconnect and try again. It does not handle
    HTTP protocol level errors (404, 500) etc.

    It will try up to tries times consecutively before giving up. A successful
    call to f will result in the try counter being reset to 0.
    """

    # pyOpenSSL has been known to throw these connection errors that need to be
    # caught separately: https://github.com/edsu/twarc/issues/72

    try:
        import OpenSSL

        ConnectionError = OpenSSL.SSL.SysCallError
    except:
        ConnectionError = requests.exceptions.ConnectionError

    @wraps(f)
    def new_f(self, *args, **kwargs):
        errors = 0
        while errors < tries:
            try:
                resp = f(self, *args, **kwargs)
                errors = 0
                return resp
            except (requests.exceptions.RequestException, ConnectionError) as e:

                # don't catch any HTTP errors since those are handled separately
                if isinstance(e, requests.exceptions.HTTPError):
                    raise e

                errors += 1
                log.warning("caught requests exception: %s", e)
                if errors > tries:
                    log.error(f"giving up, too many request exceptions: {tries}")
                    raise e
                seconds = errors ** 2
                log.info("sleeping %s", seconds)
                time.sleep(seconds)
                self.connect()

    return new_f


def interruptible_sleep(t, event=None):
    """
    Sleeps for a specified duration, optionally stopping early for event.

    Returns True if interrupted
    """
    log.info("sleeping %s", t)

    if event is None:
        time.sleep(t)
        return False
    else:
        return not event.wait(t)


class cli_api_error:
    """
    A decorator to catch HTTP errors for the command line.
    """

    def __init__(self, f):
        self.f = f
        # this is needed for click help docs to work properly
        self.__doc__ = f.__doc__

    def __call__(self, *args, **kwargs):
        try:
            return self.f(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            try:
                result = e.response.json()
                if "errors" in result:
                    for error in result["errors"]:
                        msg = error.get("message", "Unknown error")
                elif "title" in result:
                    msg = result["title"]
                else:
                    msg = "Unknown error"
            except ValueError:
                msg = f"Unable to parse {e.response.status_code} error as JSON: {e.response.text}"
        except InvalidAuthType as e:
            msg = "This command requires application authentication, try passing --app-auth"
        except ValueError as e:
            msg = str(e)
        click.echo(
            click.style("⚡ ", fg="yellow") + click.style(msg, fg="red"), err=True
        )


def requires_app_auth(f):
    """
    Ensure that application authentication is set for calls that only work in that mode.

    """

    @wraps(f)
    def new_f(self, *args, **kwargs):
        if self.auth_type != "application":
            raise InvalidAuthType(
                "This endpoint only works with application authentication"
            )

        else:
            return f(self, *args, **kwargs)

    return new_f


class InvalidAuthType(Exception):
    """
    Raised when the endpoint called is not supported by the current auth type.
    """


class FileSizeProgressBar(tqdm):
    """
    An input file size based progress bar. Counts an input file in bytes.
    This will also dig into the responses and add up the outputs to match the file size.
    Overrides `disable` parameter if file is a pipe.
    """

    def __init__(self, infile, outfile, **kwargs):
        disable = False if "disable" not in kwargs else kwargs["disable"]
        if infile is not None and (infile.name == "<stdin>"):
            disable = True
        if outfile is not None and (outfile.name == "<stdout>"):
            disable = True
        kwargs["disable"] = disable
        kwargs["unit"] = "B"
        kwargs["unit_scale"] = True
        kwargs["unit_divisor"] = 1024
        kwargs["miniters"] = 1
        kwargs[
            "bar_format"
        ] = "{l_bar}{bar}| Processed {n_fmt}/{total_fmt} of input file [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        kwargs["total"] = os.stat(infile.name).st_size if not disable else 1
        super().__init__(**kwargs)

    def update_with_result(
        self, result, field="id", error_resource_type=None, error_parameter="ids"
    ):
        try:
            for item in result["data"]:
                # Use the length of the id / name and a newline to match original file
                self.update(len(item[field]) + len("\n"))
            if error_resource_type and "errors" in result:
                for error in result["errors"]:
                    # Account for deleted data
                    # Errors have very inconsistent format, missing fields for different types of errors...
                    if (
                        "resource_type" in error
                        and error["resource_type"] == error_resource_type
                    ):
                        if (
                            "parameter" in error
                            and error["parameter"] == error_parameter
                        ):
                            self.update(len(error["value"]) + len("\n"))
                            # todo: hide or show this?
                            # self.set_description(
                            #    "Errors encountered, results may be incomplete"
                            # )
                        # print(error["value"], error["resource_type"], error["parameter"])
        except Exception as e:
            log.error(f"Failed to update progress bar: {e}")


class TimestampProgressBar(tqdm):
    """
    A Timestamp based progress bar. Counts timestamp ranges in milliseconds.
    This can be used to display a progress bar for tweet ids and time ranges.
    """

    def __init__(self, since_id, until_id, start_time, end_time, **kwargs):
        self.early_stop = True
        self.tweet_count = 0

        disable = False if "disable" not in kwargs else kwargs["disable"]
        kwargs["disable"] = disable

        if start_time is None and (since_id is None and until_id is None):
            start_time = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=7)
        if end_time is None and (since_id is None and until_id is None):
            end_time = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(seconds=30)

        if since_id and not until_id:
            until_id = _millis2snowflake(
                _date2millis(datetime.datetime.now(datetime.timezone.utc))
            )

        if until_id and not since_id:
            since_id = 1

        total = (
            _snowflake2millis(until_id) - _snowflake2millis(since_id)
            if (since_id and until_id)
            else _date2millis(end_time) - _date2millis(start_time)
        )

        kwargs["miniters"] = 1
        kwargs["total"] = total
        kwargs[
            "bar_format"
        ] = "{l_bar}{bar}| Processed {n_time}/{total_time} [{elapsed}<{remaining}, {tweet_count} tweets total {postfix}]"
        super().__init__(**kwargs)

    def update_with_result(self, result):
        """
        Update progress bar based on snowflake ids.
        """
        try:
            newest_id = result["meta"]["newest_id"]
            oldest_id = result["meta"]["oldest_id"]
            n = _snowflake2millis(int(newest_id)) - _snowflake2millis(int(oldest_id))
            self.update(n)
            self.tweet_count += len(result["data"])
        except Exception as e:
            log.error(f"Failed to update progress bar: {e}")

    @property
    def format_dict(self):
        d = super(TimestampProgressBar, self).format_dict  # original format dict
        tweets_per_second = int(self.tweet_count / d["elapsed"] if d["elapsed"] else 0)
        n_time = humanize.naturaldelta(datetime.timedelta(seconds=int(d["n"]) // 1000))
        total_time = humanize.naturaldelta(
            datetime.timedelta(seconds=int(d["total"]) // 1000)
        )
        d.update(n_time=n_time)
        d.update(total_time=total_time)
        d.update(tweet_count=self.tweet_count)
        d.update(tweets_per_second=tweets_per_second)
        return d

    def close(self):
        if not self.early_stop:
            # Finish the bar to 100% even if the last tweet ids do not cover the full time range
            self.update(self.total - self.n)
        super().close()


def _date2millis(dt):
    return int(dt.timestamp() * 1000)


def _millis2date(ms):
    return datetime.datetime.utcfromtimestamp(ms // 1000).replace(
        microsecond=ms % 1000 * 1000
    )


def _snowflake2millis(snowflake_id):
    return (snowflake_id >> 22) + 1288834974657


def _millis2snowflake(ms):
    return (int(ms) - 1288834974657) << 22
