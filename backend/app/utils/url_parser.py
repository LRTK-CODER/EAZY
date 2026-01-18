"""
URL parsing utilities for extracting query parameters.
"""

from typing import Any, Dict
from urllib.parse import parse_qs, urlparse


def parse_query_params(url: str) -> Dict[str, Any]:
    """
    Extract query parameters from a URL.

    Args:
        url: Full URL or path with query string

    Returns:
        Dictionary of parameter names to values.
        - Single values: {"key": "value"}
        - Multiple values: {"key": ["value1", "value2"]}
        - Empty query: {}

    Examples:
        >>> parse_query_params("https://example.com/search?q=test")
        {'q': 'test'}

        >>> parse_query_params("/api/users?role=admin&role=user")
        {'role': ['admin', 'user']}

        >>> parse_query_params("https://example.com/page?name=John%20Doe")
        {'name': 'John Doe'}

        >>> parse_query_params("https://example.com/")
        {}
    """
    # Parse URL
    parsed = urlparse(url)

    # parse_qs returns dict with list values
    # Example: "?key=val1&key=val2" -> {"key": ["val1", "val2"]}
    query_dict = parse_qs(parsed.query)

    # If no query string, return empty dict
    if not query_dict:
        return {}

    # Simplify single-value lists to strings
    result: Dict[str, Any] = {}
    for key, values in query_dict.items():
        if len(values) == 1:
            # Single value: store as string
            result[key] = values[0]
        else:
            # Multiple values: keep as list
            result[key] = values

    return result
