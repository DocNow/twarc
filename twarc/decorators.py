import time
import logging
import requests
import configparser
from itertools import cycle


log = logging.getLogger('twarc')


def rate_limit(f):
    """
    A decorator to handle rate limiting from the Twitter API. If
    a rate limit error is encountered we will sleep until we can
    issue the API call again.
    """
    def new_f(*args, **kwargs):
        # The twarc instance
        self = args[0]

        # Get the credentials
        config = configparser.ConfigParser()
        config.read(self.config)
        useraccounts = config.sections()

        # Create the neverending pool or carousel
        pool = cycle(useraccounts)

        # If it was note set, then it is the first
        if self.profile == '':
            self.profile = next(pool)
        rate_limit_dict = dict.fromkeys(useraccounts, 0)
        errors = 0
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                errors = 0
                return resp
            elif resp.status_code == 401:
                # Hack to retain the original exception, but augment it with
                # additional context for the user to interpret it. In a Python
                # 3 only future we can raise a new exception of the same type
                # with a new message from the old error.
                try:
                    resp.raise_for_status()
                except requests.HTTPError as e:
                    message = "\nThis is a protected or locked account, or" +\
                              " the credentials provided are no longer valid."
                    e.args = (e.args[0] + message,) + e.args[1:]
                    log.warning("401 Authentication required for %s", resp.url)
                    raise

            # Situation where we hit the rate limit
            elif resp.status_code == 429:
                reset = int(resp.headers['x-rate-limit-reset'])

                # What time is this profile going to be available again?
                rate_limit_dict[self.profile] = reset

                minimo = min(rate_limit_dict.values())
                
                if (minimo > 0):  # If one minimo is 0, then we have more to go
                    now = time.time()
                    seconds = minimo - now + 10
                    if seconds < 1:
                        seconds = 10
                    log.info(rate_limit_dict)  # Debugging

                    #Make the profile the one that has the shortest wait registred
                    self.profile = min(rate_limit_dict, key=lambda k:rate_limit_dict[k])
                    log.warning("Sleeping on {}".format(self.profile))
                    log.warning("rate limit exceeded: sleeping %s secs", seconds)
                    time.sleep(seconds)

                    # Reset the rate limit dictionary, since there was a wait 
                    # even though not all of them are going to be zero.
                    # But we'll be able to update the rate limit time
                    rate_limit_dict = dict.fromkeys(useraccounts, 0)

                else:
                    self.profile = next(pool)  # Go to the next profile
                    log.warning("Using {} credentials".format(self.profile))
                # Update the Twarc instance with the new profile. This should happen 
                # if there is a wait and if there isn't
                self.load_config()
                self.connect()

            elif resp.status_code >= 500:
                errors += 1
                if errors > 30:
                    log.warning("too many errors from Twitter, giving up")
                    resp.raise_for_status()
                seconds = 60 * errors
                log.warning("%s from Twitter API, sleeping %s",
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
    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except (requests.exceptions.ReadTimeout,
                requests.packages.urllib3.exceptions.ReadTimeoutError) as e:
            log.warning("caught read timeout: %s", e)
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
    def new_f(self, *args, **kwargs):
        for obj in f(self, *args, **kwargs):
            if self.protected == False:
                if 'user' in obj and obj['user']['protected']:
                    continue
                elif 'protected' in obj and obj['protected']:
                    continue
            yield obj

    return new_f
