"""URL resolver for converting, normalizing, and filtering crawl URLs."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


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
