"""
Scope filtering service for web crawling.

This module provides URL scope filtering based on TargetScope settings.
Uses tldextract for accurate domain extraction.

Usage:
    from app.services.scope_filter import ScopeFilter
    from app.models.target import TargetScope

    filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
    if filter.is_in_scope("https://example.com/page"):
        # URL is in scope
        pass

    # Batch filtering
    in_scope_urls = filter.filter_urls(discovered_urls)
"""

from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

import tldextract

from app.models.target import TargetScope


@lru_cache(maxsize=10000)
def extract_base_domain(hostname: str) -> str:
    """
    Extract the base (registered) domain from a hostname.

    Uses tldextract to accurately handle TLDs including ccTLDs like .co.uk.

    Args:
        hostname: Hostname to extract domain from (e.g., "api.example.com")

    Returns:
        Base domain (e.g., "example.com") or empty string if invalid

    Examples:
        >>> extract_base_domain("api.example.com")
        'example.com'

        >>> extract_base_domain("www.example.co.uk")
        'example.co.uk'
    """
    extracted = tldextract.extract(hostname)
    if not extracted.domain or not extracted.suffix:
        return ""
    return f"{extracted.domain}.{extracted.suffix}"


def _normalize_hostname(hostname: str) -> str:
    """
    Normalize hostname by removing 'www.' prefix if present.

    Args:
        hostname: Hostname to normalize

    Returns:
        Normalized hostname without www. prefix
    """
    if hostname.startswith("www."):
        return hostname[4:]
    return hostname


class ScopeFilter:
    """
    URL scope filter based on target URL and scope setting.

    Supports three scope levels:
    - DOMAIN: Only exact domain (www treated as equivalent)
    - SUBDOMAIN: Any subdomain of the base domain
    - URL_ONLY: Only URLs under the target path

    Args:
        target_url: The target URL that defines the scope
        scope: TargetScope enum value defining the scope level

    Attributes:
        target_url: Original target URL
        scope: Scope level setting
        _parsed: Parsed URL components
        _base_domain: Extracted base domain (for SUBDOMAIN scope)
        _normalized_host: Normalized hostname without www. (for DOMAIN scope)
        _target_path: Target path (for URL_ONLY scope)
    """

    def __init__(self, target_url: str, scope: TargetScope) -> None:
        """
        Initialize ScopeFilter with target URL and scope.

        Args:
            target_url: The target URL that defines the scope
            scope: TargetScope enum value (DOMAIN, SUBDOMAIN, URL_ONLY)
        """
        self.target_url = target_url
        self.scope = scope

        self._parsed = urlparse(target_url)
        self._base_domain = extract_base_domain(self._parsed.hostname or "")
        self._normalized_host = _normalize_hostname(self._parsed.hostname or "")
        self._target_path = self._parsed.path.rstrip("/") or ""

    def is_in_scope(self, url: Optional[str]) -> bool:
        """
        Check if a URL is within the configured scope.

        Args:
            url: URL to check

        Returns:
            True if URL is in scope, False otherwise

        Examples:
            >>> filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
            >>> filter.is_in_scope("https://example.com/page")
            True
            >>> filter.is_in_scope("https://api.example.com")
            False
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            if not parsed.hostname:
                return False

            hostname = parsed.hostname.lower()
            url_path = parsed.path.rstrip("/") or ""

            if self.scope == TargetScope.DOMAIN:
                return self._check_domain_scope(hostname)
            elif self.scope == TargetScope.SUBDOMAIN:
                return self._check_subdomain_scope(hostname)
            elif self.scope == TargetScope.URL_ONLY:
                return self._check_url_only_scope(hostname, url_path)

            return False

        except Exception:
            return False

    def _check_domain_scope(self, hostname: str) -> bool:
        """
        Check DOMAIN scope: exact domain match (www treated as equivalent).

        Args:
            hostname: Hostname to check

        Returns:
            True if hostname matches the target domain
        """
        normalized = _normalize_hostname(hostname)
        return normalized == self._normalized_host

    def _check_subdomain_scope(self, hostname: str) -> bool:
        """
        Check SUBDOMAIN scope: any subdomain of the base domain allowed.

        Args:
            hostname: Hostname to check

        Returns:
            True if hostname is a subdomain of the target base domain
        """
        url_base_domain = extract_base_domain(hostname)
        return url_base_domain == self._base_domain

    def _check_url_only_scope(self, hostname: str, url_path: str) -> bool:
        """
        Check URL_ONLY scope: path must be under target path.

        Args:
            hostname: Hostname to check
            url_path: Path component to check

        Returns:
            True if URL is under the target path
        """
        # First check if hostname is in subdomain scope
        if not self._check_subdomain_scope(hostname):
            return False

        # Check if path starts with target path
        if not self._target_path:
            return True

        # Path must be exactly the target path or start with target_path/
        if url_path == self._target_path:
            return True

        return url_path.startswith(self._target_path + "/")

    def filter_urls(self, urls: List[str]) -> List[str]:
        """
        Filter a list of URLs to return only in-scope URLs.

        Args:
            urls: List of URLs to filter

        Returns:
            List of URLs that are in scope (preserves order)

        Examples:
            >>> filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
            >>> filter.filter_urls(["https://example.com/a", "https://other.com"])
            ['https://example.com/a']
        """
        return [url for url in urls if self.is_in_scope(url)]


def clear_domain_cache() -> None:
    """
    Clear the extract_base_domain LRU cache.

    Useful for testing or when memory needs to be freed.
    """
    extract_base_domain.cache_clear()
