import time
import logging
import requests

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


def interruptible_sleep(t, event=None):
    """
    Sleeps for a specified duration, optionally stopping early for event.
    
    Returns True if interrupted
    """
    logging.info("sleeping %s", t)
    total_t = 0
    while total_t < t and (event is None or not event.is_set()):
        time.sleep(1)
        total_t += 1

    return True if event and event.is_set() else False


