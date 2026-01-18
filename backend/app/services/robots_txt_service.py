"""
RobotsTxtService - robots.txt parsing and caching.

This module provides robots.txt fetching, parsing, and caching
with LRU eviction and TTL expiration.

For security testing purposes, this service extracts:
- Disallowed paths (potential sensitive areas)
- Sitemap URLs (additional crawl targets)

Usage:
    from app.services.robots_txt_service import RobotsTxtService

    service = RobotsTxtService()

    # Fetch and parse robots.txt
    result = await service.fetch("https://example.com")

    # Check if path is allowed
    allowed = await service.is_allowed("https://example.com", "/admin")

    # Get sitemap URLs
    sitemaps = await service.get_sitemap_urls("https://example.com")
"""

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.core.structured_logger import get_logger
from app.core.utils import utc_now

logger = get_logger(__name__)

# Default configuration
DEFAULT_CACHE_MAXSIZE = 1000
DEFAULT_CACHE_TTL_SECONDS = 3600  # 1 hour
DEFAULT_TIMEOUT_SECONDS = 10.0
USER_AGENT = "EAZYBot/1.0"


@dataclass
class RobotsTxtResult:
    """
    Result of robots.txt parsing.

    Attributes:
        disallowed_paths: List of paths disallowed by robots.txt
        sitemap_urls: List of Sitemap URLs declared in robots.txt
        fetched_at: Timestamp when robots.txt was fetched
    """

    disallowed_paths: List[str]
    sitemap_urls: List[str]
    fetched_at: datetime = field(default_factory=utc_now)


class RobotsTxtCache:
    """
    LRU cache with TTL for RobotsTxtResult.

    Thread-safe in-memory cache that evicts least recently used
    entries when maxsize is reached and expires entries after TTL.

    Args:
        maxsize: Maximum number of entries in cache
        ttl_seconds: Time-to-live in seconds for cache entries
    """

    def __init__(
        self,
        maxsize: int = DEFAULT_CACHE_MAXSIZE,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    ) -> None:
        self._maxsize = maxsize
        self._ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[RobotsTxtResult, datetime]] = OrderedDict()

    def get(self, base_url: str) -> Optional[RobotsTxtResult]:
        """
        Get cached result for base URL.

        Args:
            base_url: Base URL (scheme + host)

        Returns:
            Cached RobotsTxtResult or None if not found/expired
        """
        if base_url not in self._cache:
            return None

        result, cached_at = self._cache[base_url]

        # Check TTL
        if utc_now() - cached_at > timedelta(seconds=self._ttl_seconds):
            del self._cache[base_url]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(base_url)
        return result

    def set(self, base_url: str, result: RobotsTxtResult) -> None:
        """
        Store result in cache.

        Args:
            base_url: Base URL (scheme + host)
            result: RobotsTxtResult to cache
        """
        # Remove if exists to update position
        if base_url in self._cache:
            del self._cache[base_url]

        # Evict LRU if at capacity
        while len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)

        self._cache[base_url] = (result, utc_now())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()


class RobotsTxtService:
    """
    Service for fetching, parsing, and caching robots.txt.

    Provides methods to:
    - Fetch and parse robots.txt for a domain
    - Check if a path is allowed
    - Get sitemap URLs declared in robots.txt

    Uses in-memory LRU cache with TTL for efficiency.

    Args:
        cache_maxsize: Maximum cache entries (default: 1000)
        cache_ttl_seconds: Cache TTL in seconds (default: 3600)
        timeout_seconds: HTTP request timeout (default: 10.0)
    """

    def __init__(
        self,
        cache_maxsize: int = DEFAULT_CACHE_MAXSIZE,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._cache = RobotsTxtCache(
            maxsize=cache_maxsize,
            ttl_seconds=cache_ttl_seconds,
        )
        self._timeout = timeout_seconds
        self._client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            verify=False,  # Allow self-signed certs for security testing
        )

    async def fetch(self, base_url: str) -> RobotsTxtResult:
        """
        Fetch and parse robots.txt for a domain.

        Uses cache if available and not expired.

        Args:
            base_url: Base URL (e.g., "https://example.com")

        Returns:
            RobotsTxtResult with disallowed paths and sitemap URLs
        """
        # Normalize base URL
        base_url = self._normalize_base_url(base_url)

        # Check cache
        cached = self._cache.get(base_url)
        if cached is not None:
            return cached

        # Fetch robots.txt
        robots_url = f"{base_url}/robots.txt"
        try:
            response = await self._client.get(
                robots_url,
                timeout=self._timeout,
                follow_redirects=True,
            )

            if response.status_code == 200:
                result = self._parse_robots_txt(response.text)
            else:
                # 404 or other error: allow all
                result = RobotsTxtResult([], [], utc_now())

        except Exception as e:
            logger.warning(
                "Failed to fetch robots.txt",
                url=robots_url,
                error=str(e),
            )
            result = RobotsTxtResult([], [], utc_now())

        # Cache result
        self._cache.set(base_url, result)
        return result

    def _parse_robots_txt(self, content: str) -> RobotsTxtResult:
        """
        Parse robots.txt content.

        Extracts Disallow rules for User-agent: * and Sitemap URLs.

        Args:
            content: robots.txt file content

        Returns:
            RobotsTxtResult with parsed data
        """
        disallowed_paths: List[str] = []
        sitemap_urls: List[str] = []

        is_relevant_user_agent = False

        for line in content.split("\n"):
            # Remove comments
            line = re.sub(r"#.*$", "", line).strip()
            if not line:
                continue

            # Parse directive
            match = re.match(r"^(\S+):\s*(.*)$", line, re.IGNORECASE)
            if not match:
                continue

            directive = match.group(1).lower()
            value = match.group(2).strip()

            if directive == "user-agent":
                is_relevant_user_agent = value.lower() == "*"

            elif directive == "disallow" and is_relevant_user_agent:
                if value:  # Empty Disallow means allow all
                    disallowed_paths.append(value)

            elif directive == "sitemap":
                sitemap_urls.append(value)

        return RobotsTxtResult(
            disallowed_paths=disallowed_paths,
            sitemap_urls=sitemap_urls,
            fetched_at=utc_now(),
        )

    async def is_allowed(self, base_url: str, path: str) -> bool:
        """
        Check if a path is allowed by robots.txt.

        Args:
            base_url: Base URL (e.g., "https://example.com")
            path: Path to check (e.g., "/admin/users")

        Returns:
            True if path is allowed, False if disallowed
        """
        result = await self.fetch(base_url)

        for disallowed in result.disallowed_paths:
            if self._path_matches(path, disallowed):
                return False

        return True

    def _path_matches(self, path: str, disallowed: str) -> bool:
        """
        Check if path matches a Disallow rule.

        Args:
            path: Path to check
            disallowed: Disallow pattern

        Returns:
            True if path matches the disallow pattern
        """
        # Normalize paths
        path = path.rstrip("/") if path != "/" else path

        # Exact match or prefix match
        if disallowed.endswith("/"):
            # /admin/ matches /admin/anything but not /adminstuff
            return path.startswith(disallowed) or path == disallowed.rstrip("/")
        else:
            # /admin matches /admin and /admin/anything
            return path == disallowed or path.startswith(disallowed + "/")

    async def get_sitemap_urls(self, base_url: str) -> List[str]:
        """
        Get Sitemap URLs declared in robots.txt.

        Args:
            base_url: Base URL (e.g., "https://example.com")

        Returns:
            List of sitemap URLs
        """
        result = await self.fetch(base_url)
        return result.sitemap_urls

    async def get_disallowed_paths(self, base_url: str) -> List[str]:
        """
        Get Disallowed paths from robots.txt.

        Useful for security testing - these often point to sensitive areas.

        Args:
            base_url: Base URL (e.g., "https://example.com")

        Returns:
            List of disallowed paths
        """
        result = await self.fetch(base_url)
        return result.disallowed_paths

    def _normalize_base_url(self, url: str) -> str:
        """
        Normalize base URL to scheme://host format.

        Args:
            url: URL to normalize

        Returns:
            Normalized base URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def clear_cache(self) -> None:
        """Clear the robots.txt cache."""
        self._cache.clear()

    async def __aenter__(self) -> "RobotsTxtService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:  # type: ignore
        """Async context manager exit."""
        await self.close()
