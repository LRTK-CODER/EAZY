"""
Tests for RobotsTxtService.

TDD Red Phase: All tests should FAIL initially until implementation.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.utils import utc_now
from app.services.robots_txt_service import (
    RobotsTxtCache,
    RobotsTxtResult,
    RobotsTxtService,
)


class TestRobotsTxtResult:
    """Tests for RobotsTxtResult dataclass."""

    def test_result_has_disallowed_paths(self):
        """Result contains disallowed paths."""
        result = RobotsTxtResult(
            disallowed_paths=["/admin", "/private"],
            sitemap_urls=[],
            fetched_at=utc_now(),
        )
        assert result.disallowed_paths == ["/admin", "/private"]

    def test_result_has_sitemap_urls(self):
        """Result contains sitemap URLs."""
        result = RobotsTxtResult(
            disallowed_paths=[],
            sitemap_urls=["https://example.com/sitemap.xml"],
            fetched_at=utc_now(),
        )
        assert result.sitemap_urls == ["https://example.com/sitemap.xml"]


class TestRobotsTxtCache:
    """Tests for in-memory LRU cache with TTL."""

    def test_cache_stores_and_retrieves(self):
        """Cache stores and retrieves result."""
        cache = RobotsTxtCache(maxsize=100, ttl_seconds=3600)
        result = RobotsTxtResult([], [], utc_now())
        cache.set("https://example.com", result)

        retrieved = cache.get("https://example.com")
        assert retrieved == result

    def test_cache_returns_none_for_missing_key(self):
        """Cache returns None for missing key."""
        cache = RobotsTxtCache(maxsize=100, ttl_seconds=3600)
        assert cache.get("https://nonexistent.com") is None

    def test_cache_expires_after_ttl(self):
        """Cache entry expires after TTL."""
        cache = RobotsTxtCache(maxsize=100, ttl_seconds=1)
        result = RobotsTxtResult([], [], utc_now() - timedelta(seconds=2))
        # Manually insert with expired timestamp
        cache._cache["https://example.com"] = (
            result,
            utc_now() - timedelta(seconds=2),
        )

        assert cache.get("https://example.com") is None

    def test_cache_evicts_lru_when_full(self):
        """Cache evicts LRU entry when maxsize reached."""
        cache = RobotsTxtCache(maxsize=2, ttl_seconds=3600)
        cache.set("https://a.com", RobotsTxtResult([], [], utc_now()))
        cache.set("https://b.com", RobotsTxtResult([], [], utc_now()))
        cache.set("https://c.com", RobotsTxtResult([], [], utc_now()))

        # First entry should be evicted
        assert cache.get("https://a.com") is None
        assert cache.get("https://b.com") is not None
        assert cache.get("https://c.com") is not None

    def test_cache_clear(self):
        """Cache can be cleared."""
        cache = RobotsTxtCache(maxsize=100, ttl_seconds=3600)
        cache.set("https://example.com", RobotsTxtResult([], [], utc_now()))
        cache.clear()
        assert cache.get("https://example.com") is None


class TestRobotsTxtServiceParsing:
    """Tests for robots.txt parsing logic."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return RobotsTxtService()

    def test_parse_disallow_rules(self, service):
        """Parses Disallow rules correctly."""
        robots_content = """
User-agent: *
Disallow: /admin
Disallow: /private/
Disallow: /api/internal
"""
        result = service._parse_robots_txt(robots_content)
        assert "/admin" in result.disallowed_paths
        assert "/private/" in result.disallowed_paths
        assert "/api/internal" in result.disallowed_paths

    def test_parse_sitemap_urls(self, service):
        """Parses Sitemap URLs correctly."""
        robots_content = """
User-agent: *
Disallow: /admin

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
"""
        result = service._parse_robots_txt(robots_content)
        assert "https://example.com/sitemap.xml" in result.sitemap_urls
        assert "https://example.com/sitemap-news.xml" in result.sitemap_urls

    def test_parse_ignores_allow_rules(self, service):
        """Allow rules are not included in disallowed paths."""
        robots_content = """
User-agent: *
Disallow: /admin
Allow: /admin/public
"""
        result = service._parse_robots_txt(robots_content)
        assert "/admin" in result.disallowed_paths
        assert "/admin/public" not in result.disallowed_paths

    def test_parse_handles_empty_disallow(self, service):
        """Empty Disallow means allow all."""
        robots_content = """
User-agent: *
Disallow:
"""
        result = service._parse_robots_txt(robots_content)
        assert result.disallowed_paths == []

    def test_parse_handles_comments(self, service):
        """Comments are ignored."""
        robots_content = """
# This is a comment
User-agent: *
Disallow: /admin  # inline comment
"""
        result = service._parse_robots_txt(robots_content)
        assert "/admin" in result.disallowed_paths

    def test_parse_handles_case_insensitive_directives(self, service):
        """Directives are case-insensitive."""
        robots_content = """
user-agent: *
DISALLOW: /admin
sitemap: https://example.com/sitemap.xml
"""
        result = service._parse_robots_txt(robots_content)
        assert "/admin" in result.disallowed_paths
        assert "https://example.com/sitemap.xml" in result.sitemap_urls

    def test_parse_specific_user_agent_disallow(self, service):
        """Parses Disallow for specific user-agent (uses * rules by default)."""
        robots_content = """
User-agent: Googlebot
Disallow: /google-only

User-agent: *
Disallow: /admin
"""
        # Default behavior: use * rules
        result = service._parse_robots_txt(robots_content)
        assert "/admin" in result.disallowed_paths
        # /google-only should NOT be in disallowed for *
        assert "/google-only" not in result.disallowed_paths

    def test_parse_empty_robots_txt(self, service):
        """Empty robots.txt means allow all."""
        result = service._parse_robots_txt("")
        assert result.disallowed_paths == []
        assert result.sitemap_urls == []


class TestRobotsTxtServiceFetch:
    """Tests for fetching robots.txt."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return RobotsTxtService()

    @pytest.mark.asyncio
    async def test_fetch_robots_txt_success(self, service):
        """Successfully fetches and parses robots.txt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
User-agent: *
Disallow: /admin
Sitemap: https://example.com/sitemap.xml
"""

        with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await service.fetch("https://example.com")

            assert "/admin" in result.disallowed_paths
            assert "https://example.com/sitemap.xml" in result.sitemap_urls
            mock_get.assert_called_once_with(
                "https://example.com/robots.txt",
                timeout=10.0,
                follow_redirects=True,
            )

    @pytest.mark.asyncio
    async def test_fetch_robots_txt_404_returns_empty(self, service):
        """404 response returns empty result (allow all)."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await service.fetch("https://example.com")

            assert result.disallowed_paths == []
            assert result.sitemap_urls == []

    @pytest.mark.asyncio
    async def test_fetch_robots_txt_timeout_returns_empty(self, service):
        """Timeout returns empty result."""
        with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = TimeoutError()
            result = await service.fetch("https://example.com")

            assert result.disallowed_paths == []
            assert result.sitemap_urls == []

    @pytest.mark.asyncio
    async def test_fetch_uses_cache(self, service):
        """Second fetch uses cached result."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /admin"

        with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # First fetch
            result1 = await service.fetch("https://example.com")
            # Second fetch (should use cache)
            result2 = await service.fetch("https://example.com")

            assert result1.disallowed_paths == result2.disallowed_paths
            # HTTP request should only be made once
            assert mock_get.call_count == 1


class TestRobotsTxtServiceIsAllowed:
    """Tests for is_allowed method."""

    @pytest.fixture
    def service(self):
        """Create service instance with pre-populated cache."""
        service = RobotsTxtService()
        # Pre-populate cache
        result = RobotsTxtResult(
            disallowed_paths=["/admin", "/private/", "/api/internal"],
            sitemap_urls=[],
            fetched_at=utc_now(),
        )
        service._cache.set("https://example.com", result)
        return service

    @pytest.mark.asyncio
    async def test_is_allowed_returns_true_for_allowed_path(self, service):
        """Returns True for allowed path."""
        assert await service.is_allowed("https://example.com", "/public/page") is True

    @pytest.mark.asyncio
    async def test_is_allowed_returns_false_for_disallowed_path(self, service):
        """Returns False for disallowed path."""
        assert await service.is_allowed("https://example.com", "/admin") is False

    @pytest.mark.asyncio
    async def test_is_allowed_matches_prefix(self, service):
        """Disallow matches path prefix."""
        assert await service.is_allowed("https://example.com", "/admin/users") is False

    @pytest.mark.asyncio
    async def test_is_allowed_trailing_slash_handling(self, service):
        """Correctly handles trailing slash in Disallow."""
        # /private/ should match /private/anything but not /privatestuff
        assert (
            await service.is_allowed("https://example.com", "/private/secret") is False
        )
        assert await service.is_allowed("https://example.com", "/privatestuff") is True


class TestRobotsTxtServiceGetSitemapUrls:
    """Tests for get_sitemap_urls method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return RobotsTxtService()

    @pytest.mark.asyncio
    async def test_get_sitemap_urls_returns_list(self, service):
        """Returns list of sitemap URLs."""
        result = RobotsTxtResult(
            disallowed_paths=[],
            sitemap_urls=[
                "https://example.com/sitemap.xml",
                "https://example.com/sitemap-news.xml",
            ],
            fetched_at=utc_now(),
        )
        service._cache.set("https://example.com", result)

        sitemaps = await service.get_sitemap_urls("https://example.com")
        assert len(sitemaps) == 2
        assert "https://example.com/sitemap.xml" in sitemaps
