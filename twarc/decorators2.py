import time
import click
import types
import logging
import requests

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

                # don't catch any HTTP erorrs since those are handled separately
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
