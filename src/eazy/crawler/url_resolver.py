"""URL resolver for converting, normalizing, and filtering crawl URLs."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse


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
