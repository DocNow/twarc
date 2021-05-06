"""
Useful functions for converting things into different types
"""

def _ts(dt):
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
    return dt.isoformat(timespec='seconds')

def _utcnow():
    """
    Return _now_ in ISO 8601 / RFC 3339 datetime in UTC.

    Returns:
        datetime: Current timestamp in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec='seconds'
    )
