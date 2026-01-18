"""
Core utilities package.

Provides common utility classes and functions for the EAZY backend.
"""

from app.core.utils.datetime import utc_now, utc_now_tz
from app.core.utils.json_parser import JsonParseResult, SafeJsonParser

__all__ = ["SafeJsonParser", "JsonParseResult", "utc_now", "utc_now_tz"]
