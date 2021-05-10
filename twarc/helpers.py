"""
Useful functions for converting things into different types
"""
import datetime


def ts(dt):
    """
    Return ISO 8601 / RFC 3339 datetime in UTC. If no timezone is specified it
    is assumed to be in UTC. The Twitter API does not accept microseconds.

    Args:
        dt (datetime): a `datetime` object to format.

    Returns:
        str: an ISO 8601 / RFC 3339 datetime in UTC.
    """
    if dt.tzinfo:
        dt = dt.astimezone(datetime.timezone.utc)
    else:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat(timespec="seconds")


def utcnow():
    """
    Return _now_ in ISO 8601 / RFC 3339 datetime in UTC.

    Returns:
        datetime: Current timestamp in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _snowflake2millis(snowflake_id):
    return (snowflake_id >> 22) + 1288834974657


def _millis2snowflake(milliseconds):
    return (int(milliseconds) - 1288834974657) << 22


def _get_millis(ms):
    return ms % 1000


def _sample_windows(start_ts, end_ts, sample_type):
    """
    todo: Generate tuples of start and end snowflake ids between two timestamps
    
    sample_type - type of random sample and millisecond range:
        _1% "Spritzer" Sample   [657-666]
        10% "Gardenhose" Sample [657-756]
        10% "Enterprise" Sample [*0*]
        _1% v2 Sample           [?]
        _N% v2 Sample           [?]
    """
    pass
