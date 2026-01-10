"""Datetime utilities for EAZY project.

This module provides timezone-aware and timezone-naive datetime functions
for different use cases:

- utc_now(): Returns offset-naive UTC datetime for PostgreSQL compatibility
- utc_now_tz(): Returns timezone-aware UTC datetime for ISO format/Redis

Background:
    PostgreSQL TIMESTAMP (without time zone) expects offset-naive datetimes.
    Redis/JSON storage prefers timezone-aware datetimes with ISO format.
    Mixing these types in datetime arithmetic causes TypeError.

Usage:
    # For database fields (SQLAlchemy DateTime)
    from app.core.utils import utc_now
    task.created_at = utc_now()

    # For Redis/JSON storage with ISO format
    from app.core.utils import utc_now_tz
    data = {"timestamp": utc_now_tz().isoformat()}

    # For parsing ISO strings from Redis
    parsed = datetime.fromisoformat(redis_value)
    elapsed = (utc_now_tz() - parsed).total_seconds()  # No TypeError
"""

from datetime import datetime, timezone

__all__ = ["utc_now", "utc_now_tz"]


def utc_now() -> datetime:
    """Return current UTC datetime as offset-naive (for PostgreSQL).

    PostgreSQL TIMESTAMP columns expect offset-naive datetimes.
    SQLAlchemy's DateTime type maps to TIMESTAMP by default.

    Returns:
        datetime: Current UTC time with tzinfo=None

    Example:
        >>> from app.core.utils import utc_now
        >>> now = utc_now()
        >>> now.tzinfo is None
        True
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_tz() -> datetime:
    """Return current UTC datetime as timezone-aware (for ISO format).

    Use this when storing timestamps as ISO strings in Redis/JSON,
    or when doing datetime arithmetic with parsed ISO strings.

    Returns:
        datetime: Current UTC time with tzinfo=timezone.utc

    Example:
        >>> from app.core.utils import utc_now_tz
        >>> now = utc_now_tz()
        >>> now.tzinfo == timezone.utc
        True
        >>> "+00:00" in now.isoformat()
        True
    """
    return datetime.now(timezone.utc)
