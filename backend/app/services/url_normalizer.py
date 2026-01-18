"""
URL Normalization service for deduplication in crawling.

This module provides URL normalization functions to ensure consistent
URL representation for duplicate detection during web crawling.

Usage:
    from app.services.url_normalizer import normalize_url, get_url_hash

    # Normalize a URL
    normalized = normalize_url("HTTPS://EXAMPLE.COM/page#section")
    # Result: "https://example.com/page"

    # Get hash for deduplication
    url_hash = get_url_hash("https://example.com/page", method="GET")

    # Compare URLs
    same = is_same_resource(url1, url2)

    # Batch normalization
    normalized_urls = normalize_urls_batch(urls, base_url="https://example.com")
"""

import hashlib
import re
from functools import lru_cache
from typing import NewType, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

# Type alias for normalized URLs (zero runtime overhead)
NormalizedUrl = NewType("NormalizedUrl", str)

# Default ports for common schemes
DEFAULT_PORTS: dict[str, int] = {
    "http": 80,
    "https": 443,
}

# Pre-compiled regex for duplicate slashes (performance optimization)
_DUPLICATE_SLASH_PATTERN = re.compile(r"/+")


@lru_cache(maxsize=10000)
def normalize_url(url: str, base_url: Optional[str] = None) -> NormalizedUrl:
    """
    Normalize a URL for consistent representation.

    Normalization rules applied:
    1. Resolve relative URLs to absolute (if base_url provided)
    2. Lowercase scheme and host
    3. Remove default ports (:80 for HTTP, :443 for HTTPS)
    4. Remove fragment (#section)
    5. Sort query parameters alphabetically (preserve empty values)
    6. Remove trailing slash (except for root path)
    7. Normalize duplicate slashes in path

    Args:
        url: URL to normalize (can be relative if base_url provided)
        base_url: Base URL for resolving relative URLs

    Returns:
        Normalized URL string

    Raises:
        ValueError: If URL is empty or None

    Examples:
        >>> normalize_url("HTTPS://EXAMPLE.COM/page#section")
        'https://example.com/page'

        >>> normalize_url("../other", base_url="https://example.com/path/page")
        'https://example.com/other'

        >>> normalize_url("https://example.com/search?z=3&a=1")
        'https://example.com/search?a=1&z=3'
    """
    # Validate input
    if not url:
        raise ValueError("URL cannot be empty or None")

    # Resolve relative URL if base_url provided
    if base_url and not _is_absolute_url(url):
        url = urljoin(base_url, url)

    # Parse the URL
    parsed = urlparse(url)

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ""

    # Handle port - remove if it's the default for the scheme
    port = parsed.port
    if port and DEFAULT_PORTS.get(scheme) == port:
        port = None

    # Build netloc (host:port)
    netloc = host
    if port:
        netloc = f"{host}:{port}"

    # Normalize path - remove duplicate slashes and trailing slash
    path = _normalize_path(parsed.path)

    # Sort query parameters (preserve empty values)
    query = _normalize_query(parsed.query)

    # Fragment is removed (set to empty string)
    fragment = ""

    # Reconstruct the URL
    normalized = urlunparse((scheme, netloc, path, "", query, fragment))

    return NormalizedUrl(normalized)


def get_url_hash(url: str, method: str = "GET") -> str:
    """
    Generate a SHA-256 hash for URL deduplication.

    The hash is generated from the normalized URL combined with
    the HTTP method, allowing different methods to the same URL
    to be tracked separately.

    Args:
        url: URL to hash
        method: HTTP method (default: "GET")

    Returns:
        SHA-256 hex digest (64 characters)

    Examples:
        >>> get_url_hash("https://example.com/page")
        '...'  # 64-character hex string

        >>> get_url_hash("https://example.com/api", method="POST")
        '...'  # Different hash from GET
    """
    normalized = normalize_url(url)
    content = f"{method.upper()}:{normalized}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_same_resource(url1: str, url2: str) -> bool:
    """
    Check if two URLs point to the same resource.

    Compares URLs after normalization to determine if they
    represent the same resource, ignoring formatting differences.

    Args:
        url1: First URL to compare
        url2: Second URL to compare

    Returns:
        True if URLs point to the same resource, False otherwise

    Examples:
        >>> is_same_resource(
        ...     "https://example.com/page#section",
        ...     "HTTPS://EXAMPLE.COM/page/"
        ... )
        True

        >>> is_same_resource(
        ...     "https://example.com/page1",
        ...     "https://example.com/page2"
        ... )
        False
    """
    return normalize_url(url1) == normalize_url(url2)


def _is_absolute_url(url: str) -> bool:
    """Check if URL is absolute (has scheme)."""
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def _normalize_path(path: str) -> str:
    """
    Normalize URL path.

    - Remove duplicate slashes
    - Remove trailing slash (including root path)
    """
    if not path:
        return ""

    # Remove duplicate slashes (using pre-compiled pattern)
    path = _DUPLICATE_SLASH_PATTERN.sub("/", path)

    # Remove trailing slash (including root "/" -> "")
    if path.endswith("/"):
        path = path.rstrip("/")

    return path


def _normalize_query(query: str) -> str:
    """
    Normalize query string.

    - Sort parameters alphabetically
    - Preserve empty values
    """
    if not query:
        return ""

    # Parse query string (keep_blank_values=True to preserve empty values)
    params = parse_qs(query, keep_blank_values=True)

    # Sort parameters and flatten lists
    sorted_params = []
    for key in sorted(params.keys()):
        for value in params[key]:
            sorted_params.append((key, value))

    # Encode back to query string
    return urlencode(sorted_params)


def normalize_urls_batch(
    urls: list[str], base_url: Optional[str] = None
) -> list[NormalizedUrl]:
    """
    Normalize multiple URLs in batch.

    Useful for processing discovered URLs during crawling.
    Leverages lru_cache for repeated URLs.

    Args:
        urls: List of URLs to normalize
        base_url: Base URL for resolving relative URLs

    Returns:
        List of normalized URLs

    Examples:
        >>> normalize_urls_batch([
        ...     "https://example.com/page1",
        ...     "HTTPS://EXAMPLE.COM/page2#section"
        ... ])
        ['https://example.com/page1', 'https://example.com/page2']
    """
    return [normalize_url(url, base_url) for url in urls]


def clear_cache() -> None:
    """
    Clear the normalize_url LRU cache.

    Useful for testing or when memory needs to be freed.
    """
    normalize_url.cache_clear()
