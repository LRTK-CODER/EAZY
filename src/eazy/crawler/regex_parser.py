"""Regex-based HTML parser for extracting page structure."""

from __future__ import annotations

import re

# Compile regex pattern at module level for performance
HREF_PATTERN = re.compile(r'href\s*=\s*["\'](.*?)["\']', re.IGNORECASE)

# Protocols to filter out
EXCLUDED_PROTOCOLS = ('javascript:', 'mailto:', 'tel:')


def extract_links(html: str) -> list[str]:
    """Extract all valid HTTP/HTTPS links from HTML.

    Args:
        html: Raw HTML content to parse.

    Returns:
        List of URL strings found in href attributes. Empty list if no links found.
        Filters out javascript:, mailto:, and tel: protocol URLs.
    """
    matches = HREF_PATTERN.findall(html)
    return [
        url for url in matches
        if not url.startswith(EXCLUDED_PROTOCOLS)
    ]
