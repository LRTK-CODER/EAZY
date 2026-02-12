"""URL resolver for converting, normalizing, and filtering crawl URLs."""

from __future__ import annotations

import fnmatch
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from eazy.models.crawl_types import CrawlConfig


def resolve_url(base_url: str, href: str) -> str | None:
    """Resolve a raw href to an absolute URL.

    Args:
        base_url: The page URL where the href was found.
        href: The raw href value extracted from HTML.

    Returns:
        Absolute URL string, or None if the href is empty or fragment-only.
    """
    if not href or href.startswith("#"):
        return None

    resolved = urljoin(base_url, href)

    # For protocol-relative URLs, urljoin handles them correctly
    # by inheriting the scheme from base_url
    parsed = urlparse(resolved)
    if not parsed.scheme or not parsed.netloc:
        return None

    return resolved


# Default ports per scheme for normalization
_DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize_url(url: str) -> str:
    """Normalize a URL for consistent deduplication.

    Args:
        url: Absolute URL to normalize.

    Returns:
        Normalized URL with lowercase scheme/host, default ports removed,
        fragment stripped, trailing slash removed, and query params sorted.
    """
    parsed = urlparse(url)

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ""

    # Remove default ports
    port = parsed.port
    if port and port == _DEFAULT_PORTS.get(scheme):
        port = None

    netloc = host
    if port:
        netloc = f"{host}:{port}"

    # Remove trailing slash (but keep root "/" as-is)
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Sort query parameters
    query = ""
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)

    # Rebuild without fragment
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def is_in_scope(url: str, config: CrawlConfig) -> bool:
    """Check whether a URL falls within the crawl scope.

    Args:
        url: Absolute URL to check.
        config: Crawl configuration with target_url, include_subdomains,
            and exclude_patterns.

    Returns:
        True if the URL is within scope, False otherwise.
    """
    parsed_url = urlparse(url)
    parsed_target = urlparse(config.target_url)

    url_host = parsed_url.hostname or ""
    target_host = parsed_target.hostname or ""

    # Domain check
    if config.include_subdomains:
        if url_host != target_host and not url_host.endswith(f".{target_host}"):
            return False
    else:
        if url_host != target_host:
            return False

    # Path prefix check
    target_path = parsed_target.path.rstrip("/")
    if target_path:
        url_path = parsed_url.path
        if not url_path.startswith(target_path):
            return False

    # Exclude patterns check
    url_path = parsed_url.path
    for pattern in config.exclude_patterns:
        if fnmatch.fnmatch(url_path, pattern) or fnmatch.fnmatch(url, pattern):
            return False

    return True
