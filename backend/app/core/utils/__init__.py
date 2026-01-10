"""
Core utilities package.

Provides common utility classes and functions for the EAZY backend.
"""
from app.core.utils.json_parser import SafeJsonParser, JsonParseResult

__all__ = ["SafeJsonParser", "JsonParseResult"]
