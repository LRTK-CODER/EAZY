"""Integration tests for the crawler engine."""

from __future__ import annotations

import httpx
import respx

from eazy.crawler.engine import CrawlerEngine
from eazy.models.crawl_types import CrawlConfig


class TestBasicCrawling:
    """Test basic crawling behavior."""

    @respx.mock
    async def test_crawl_single_page(self) -> None:
        """Single page with no links produces one PageResult."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><head><title>Home</title></head><body>Hello</body></html>"
                ),
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 1
        assert result.pages[0].url == "https://example.com"
        assert result.pages[0].title == "Home"
        assert result.pages[0].status_code == 200
        assert result.pages[0].depth == 0
        assert result.pages[0].error is None

    @respx.mock
    async def test_crawl_follows_links(self) -> None:
        """Crawler follows discovered links to new pages."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/about">About</a></body></html>'),
            )
        )
        respx.get("https://example.com/about").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><head><title>About</title></head>"
                    "<body>About us</body></html>"
                ),
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 2
        urls = {p.url for p in result.pages}
        assert "https://example.com" in urls
        assert "https://example.com/about" in urls

    @respx.mock
    async def test_crawl_deduplicates_urls(self) -> None:
        """Same URL is never visited twice (circular links)."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/other">Other</a></body></html>'),
            )
        )
        respx.get("https://example.com/other").mock(
            return_value=httpx.Response(
                200,
                text=(
                    '<html><body><a href="https://example.com">Back</a></body></html>'
                ),
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 2

    @respx.mock
    async def test_crawl_tracks_parent_url(self) -> None:
        """Parent URL is correctly set for discovered pages."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/about">About</a></body></html>'),
            )
        )
        respx.get("https://example.com/about").mock(
            return_value=httpx.Response(
                200,
                text="<html><body>About page</body></html>",
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        root = next(p for p in result.pages if p.url == "https://example.com")
        about = next(p for p in result.pages if p.url == "https://example.com/about")
        assert root.parent_url is None
        assert about.parent_url == "https://example.com"


class TestCrawlConfiguration:
    """Test crawl configuration options."""

    @respx.mock
    async def test_crawl_respects_max_depth(self) -> None:
        """Crawler stops following links beyond max_depth."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            max_depth=0,
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/deep">Deep</a></body></html>'),
            )
        )
        respx.get("https://example.com/deep").mock(
            return_value=httpx.Response(200, text="<html>Deep</html>")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 1
        assert result.pages[0].url == "https://example.com"

    @respx.mock
    async def test_crawl_respects_max_pages(self) -> None:
        """Crawler stops after reaching max_pages limit."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            max_pages=2,
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/a">A</a>'
                    '<a href="/b">B</a>'
                    '<a href="/c">C</a>'
                    "</body></html>"
                ),
            )
        )
        respx.get("https://example.com/a").mock(
            return_value=httpx.Response(200, text="<html>A</html>")
        )
        respx.get("https://example.com/b").mock(
            return_value=httpx.Response(200, text="<html>B</html>")
        )
        respx.get("https://example.com/c").mock(
            return_value=httpx.Response(200, text="<html>C</html>")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 2

    @respx.mock
    async def test_crawl_respects_domain_scope(self) -> None:
        """Crawler ignores links to external domains."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="https://external.com/page">'
                    "External</a>"
                    '<a href="/internal">Internal</a>'
                    "</body></html>"
                ),
            )
        )
        respx.get("https://example.com/internal").mock(
            return_value=httpx.Response(200, text="<html>Internal</html>")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        urls = {p.url for p in result.pages}
        assert "https://example.com" in urls
        assert "https://example.com/internal" in urls
        assert "https://external.com/page" not in urls

    @respx.mock
    async def test_crawl_respects_robots_txt(self) -> None:
        """Crawler obeys robots.txt Disallow rules."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=True,
        )
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(
                200,
                text="User-agent: *\nDisallow: /secret\n",
            )
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/public">Public</a>'
                    '<a href="/secret">Secret</a>'
                    "</body></html>"
                ),
            )
        )
        respx.get("https://example.com/public").mock(
            return_value=httpx.Response(200, text="<html>Public</html>")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        urls = {p.url for p in result.pages}
        assert "https://example.com/public" in urls
        assert "https://example.com/secret" not in urls

    @respx.mock
    async def test_crawl_applies_exclude_patterns(self) -> None:
        """Exclude patterns filter out matching URLs."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            exclude_patterns=["*.pdf"],
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/page">Page</a>'
                    '<a href="/doc.pdf">PDF</a>'
                    "</body></html>"
                ),
            )
        )
        respx.get("https://example.com/page").mock(
            return_value=httpx.Response(200, text="<html>Page</html>")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        urls = {p.url for p in result.pages}
        assert "https://example.com/page" in urls
        assert "https://example.com/doc.pdf" not in urls


class TestPatternNormalization:
    """Test URL pattern normalization integration."""

    @respx.mock
    async def test_crawl_with_pattern_normalization_skips_duplicate_patterns(
        self,
    ) -> None:
        """Pattern normalization skips URLs beyond max_samples."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=True,
            max_samples_per_pattern=3,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/posts/1">P1</a>'
                    '<a href="/posts/2">P2</a>'
                    '<a href="/posts/3">P3</a>'
                    '<a href="/posts/4">P4</a>'
                    "</body></html>"
                ),
            )
        )
        for i in range(1, 5):
            respx.get(f"https://example.com/posts/{i}").mock(
                return_value=httpx.Response(
                    200,
                    text=f"<html><body>Post {i}</body></html>",
                )
            )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert — root + 3 posts sampled, 4th skipped
        assert len(result.pages) == 4

    @respx.mock
    async def test_crawl_without_pattern_normalization_crawls_all(
        self,
    ) -> None:
        """Disabled normalization crawls every URL."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/posts/1">P1</a>'
                    '<a href="/posts/2">P2</a>'
                    '<a href="/posts/3">P3</a>'
                    '<a href="/posts/4">P4</a>'
                    "</body></html>"
                ),
            )
        )
        for i in range(1, 5):
            respx.get(f"https://example.com/posts/{i}").mock(
                return_value=httpx.Response(
                    200,
                    text=f"<html><body>Post {i}</body></html>",
                )
            )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert — all 5 pages crawled
        assert len(result.pages) == 5

    @respx.mock
    async def test_crawl_result_includes_pattern_groups(self) -> None:
        """CrawlResult includes pattern_groups when normalization enabled."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=True,
            max_samples_per_pattern=3,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/posts/1">P1</a>'
                    '<a href="/posts/2">P2</a>'
                    "</body></html>"
                ),
            )
        )
        for i in range(1, 3):
            respx.get(f"https://example.com/posts/{i}").mock(
                return_value=httpx.Response(
                    200,
                    text=f"<html><body>Post {i}</body></html>",
                )
            )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert result.pattern_groups is not None
        assert len(result.pattern_groups.groups) >= 1

    @respx.mock
    async def test_crawl_pattern_normalization_statistics(self) -> None:
        """Pattern normalization statistics are accurate."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=True,
            max_samples_per_pattern=3,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=(
                    "<html><body>"
                    '<a href="/posts/1">P1</a>'
                    '<a href="/posts/2">P2</a>'
                    '<a href="/posts/3">P3</a>'
                    "</body></html>"
                ),
            )
        )
        for i in range(1, 4):
            respx.get(f"https://example.com/posts/{i}").mock(
                return_value=httpx.Response(
                    200,
                    text=f"<html><body>Post {i}</body></html>",
                )
            )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert — root + 3 posts = 4 processed
        assert result.pattern_groups is not None
        assert result.pattern_groups.total_urls_processed == 4
        # root pattern (/) + posts pattern (/posts/<int>)
        assert result.pattern_groups.total_patterns_found == 2


class TestFullWorkflow:
    """Test full crawl workflow and result structure."""

    @respx.mock
    async def test_crawl_returns_complete_metadata(self) -> None:
        """CrawlResult contains all expected metadata fields."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text="<html><body>Hello</body></html>",
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert result.target_url == "https://example.com"
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.started_at <= result.completed_at
        assert result.config == config

    @respx.mock
    async def test_crawl_result_contains_statistics(self) -> None:
        """CrawlResult includes accurate statistics."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/about">About</a></body></html>'),
            )
        )
        respx.get("https://example.com/about").mock(
            return_value=httpx.Response(
                200,
                text="<html><body>About us</body></html>",
            )
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert result.statistics["total_pages"] == 2
        assert "total_links" in result.statistics
        assert "total_forms" in result.statistics
        assert "total_endpoints" in result.statistics

    @respx.mock
    async def test_crawl_handles_http_error_page(self) -> None:
        """404 pages are recorded with error field set."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text=('<html><body><a href="/missing">Missing</a></body></html>'),
            )
        )
        respx.get("https://example.com/missing").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 2
        error_page = next(
            p for p in result.pages if p.url == "https://example.com/missing"
        )
        assert error_page.status_code == 404
        assert error_page.error is not None

    @respx.mock
    async def test_crawl_handles_connection_error(self) -> None:
        """Connection errors are recorded with error field set."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            max_retries=0,
            respect_robots=False,
        )
        respx.get("https://example.com/").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        # Act
        engine = CrawlerEngine(config)
        result = await engine.crawl()

        # Assert
        assert len(result.pages) == 1
        assert result.pages[0].error is not None
        assert result.pages[0].status_code == 0
