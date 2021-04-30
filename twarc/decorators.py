import time
import click
import logging
from functools import wraps

from requests import HTTPError
from requests.packages.urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ChunkedEncodingError, ReadTimeout, \
                                ContentDecodingError


log = logging.getLogger('twarc')


class InvalidAuthType(Exception):
    """
    Raised when the endpoint called is not supported by the current auth type.
    """


def rate_limit(f):
    """
    A decorator to handle rate limiting from the Twitter API. If
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
            elif resp.status_code == 401:
                # Hack to retain the original exception, but augment it with
                # additional context for the user to interpret it. In a Python
                # 3 only future we can raise a new exception of the same type
                # with a new message from the old error.
                try:
                    resp.raise_for_status()
                except HTTPError as e:
                    message = "\nThis is a protected or locked account, or" +\
                              " the credentials provided are no longer valid."
                    e.args = (e.args[0] + message,) + e.args[1:]
                    log.warning("401 Authentication required for %s", resp.url)
                    raise
            elif resp.status_code == 429:
                try:
                    reset = int(resp.headers['x-rate-limit-reset'])
                    now = time.time()
                    seconds = reset - now + 10
                except KeyError:
                    # gnip endpoint doesn't have x-rate-limit-reset
                    seconds = 2
                if seconds < 1:
                    seconds = 10
                log.warning("rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            elif resp.status_code >= 500:
                errors += 1
                if errors > 30:
                    log.warning("too many errors from Twitter, giving up")
                    resp.raise_for_status()
                seconds = 60 * errors
                log.warning("%s from Twitter API, sleeping %s",
                             resp.status_code, seconds)
                time.sleep(seconds)
            elif resp.status_code== 422:
                log.error("Recieved HTTP 422 response from Twitter API. Are you using the Premium API and forgot to use --sandbox or sandbox parameter?")
                return resp
            else:
                resp.raise_for_status()
    return new_f


def catch_conn_reset(f):
    """
    A decorator to handle connection reset errors even ones from pyOpenSSL
    until https://github.com/edsu/twarc/issues/72 is resolved
    It also handles ChunkedEncodingError which has been observed in the wild.
    """
    try:
        import OpenSSL
        ConnectionError = OpenSSL.SSL.SysCallError
    except:
        ConnectionError = None

    @wraps(f)
    def new_f(self, *args, **kwargs):
        # Only handle if pyOpenSSL is installed.
        if ConnectionError:
            try:
                return f(self, *args, **kwargs)
            except (ConnectionError, ChunkedEncodingError) as e:
                log.warning("caught connection reset error: %s", e)
                self.connect()
                return f(self, *args, **kwargs)
        else:
            return f(self, *args, **kwargs)
    return new_f


def catch_timeout(f):
    """
    A decorator to handle read timeouts from Twitter.
    """
    @wraps(f)
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except (ReadTimeout, ReadTimeoutError) as e:
            log.warning("caught read timeout: %s", e)
            self.connect()
            return f(self, *args, **kwargs)
    return new_f


def catch_gzip_errors(f):
    """
    A decorator to handle gzip encoding errors which have been known to
    happen during hydration.
    """
    @wraps(f)
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except ContentDecodingError as e:
            log.warning("caught gzip error: %s", e)
            self.connect()
            return f(self, *args, **kwargs)
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

def filter_protected(f):
    """
    filter_protected will filter out protected tweets and users unless
    explicitly requested not to.
    """
    @wraps(f)
    def new_f(self, *args, **kwargs):
        for obj in f(self, *args, **kwargs):
            if self.protected == False:
                if 'user' in obj and obj['user']['protected']:
                    continue
                elif 'protected' in obj and obj['protected']:
                    continue
            yield obj

    return new_f

class cli_api_error():
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
        except HTTPError as e:
            try:
                result = e.response.json()
                if 'errors' in result:
                    for error in result['errors']:
                        msg = error.get('message', 'Unknown error')
                elif 'title' in result:
                    msg = result['title']
                else:
                    msg = 'Unknown error'
            except ValueError:
                msg = f'Unable to parse {e.response.status_code} error as JSON: {e.response.text}'
        except InvalidAuthType as e:
            msg = "This command requires application authentication, try passing --app-auth"
        except ValueError as e:
            msg = str(e)
        click.echo(
            click.style("⚡ ", fg="yellow") + click.style(msg, fg="red"),
            err=True
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
