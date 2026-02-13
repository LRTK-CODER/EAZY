"""BFS-based async crawler engine integrating all crawl modules."""

from __future__ import annotations

import re
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urlparse

from eazy.crawler.http_client import HttpClient, HttpResponse
from eazy.crawler.regex_parser import (
    extract_api_endpoints,
    extract_buttons,
    extract_forms,
    extract_links,
)
from eazy.crawler.robots_parser import RobotsParser
from eazy.crawler.sitemap import Sitemap
from eazy.crawler.url_pattern import URLPatternNormalizer
from eazy.crawler.url_resolver import is_in_scope, normalize_url, resolve_url
from eazy.models.crawl_types import CrawlConfig, CrawlResult, PageResult

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class CrawlerEngine:
    """BFS-based async crawling engine.

    Integrates HttpClient, regex_parser, url_resolver, robots_parser,
    and Sitemap to perform a complete crawl from a target URL.

    Args:
        config: Crawl configuration.
    """

    def __init__(self, config: CrawlConfig) -> None:
        self._config = config
        self._sitemap = Sitemap()
        self._visited: set[str] = set()
        self._robots: RobotsParser | None = None
        self._normalizer: URLPatternNormalizer | None = (
            URLPatternNormalizer(max_samples=config.max_samples_per_pattern)
            if config.enable_pattern_normalization
            else None
        )

    async def crawl(self) -> CrawlResult:
        """Run a BFS crawl and return the result.

        Returns:
            CrawlResult with all discovered pages and statistics.
        """
        started_at = datetime.now(tz=timezone.utc)

        async with HttpClient(self._config) as client:
            if self._config.respect_robots:
                await self._fetch_robots(client)

            target = normalize_url(self._config.target_url)
            queue: deque[tuple[str, int, str | None]] = deque()
            queue.append((target, 0, None))

            while queue:
                if (
                    self._config.max_pages is not None
                    and len(self._visited) >= self._config.max_pages
                ):
                    break

                url, depth, parent_url = queue.popleft()

                if url in self._visited:
                    continue
                if depth > self._config.max_depth:
                    continue
                if not is_in_scope(url, self._config):
                    continue
                if self._robots and not self._robots.is_allowed(
                    url, self._config.user_agent
                ):
                    continue
                if self._normalizer and self._normalizer.should_skip(url):
                    continue

                self._visited.add(url)
                response = await client.fetch(url)
                page = self._build_page_result(response, url, depth, parent_url)
                self._sitemap.add_page(page)
                if self._normalizer:
                    self._normalizer.add_url(url)

                if not response.error and response.status_code < 400:
                    for link in page.links:
                        if link not in self._visited:
                            queue.append((link, depth + 1, url))

        completed_at = datetime.now(tz=timezone.utc)
        return CrawlResult(
            target_url=self._config.target_url,
            started_at=started_at,
            completed_at=completed_at,
            config=self._config,
            pages=self._sitemap.pages,
            statistics=self._sitemap.get_statistics(),
            pattern_groups=(
                self._normalizer.get_results() if self._normalizer else None
            ),
        )

    async def _fetch_robots(self, client: HttpClient) -> None:
        """Fetch and parse robots.txt from the target domain.

        Args:
            client: HTTP client to use for the request.
        """
        parsed = urlparse(self._config.target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        response = await client.fetch(robots_url)
        body = response.body if not response.error else ""
        self._robots = RobotsParser(body)

    def _build_page_result(
        self,
        response: HttpResponse,
        url: str,
        depth: int,
        parent_url: str | None,
    ) -> PageResult:
        """Build a PageResult from an HTTP response.

        Args:
            response: The HTTP response for this page.
            url: Normalized URL of the page.
            depth: BFS depth from the root.
            parent_url: URL of the page that linked here.

        Returns:
            PageResult with extracted page structure.
        """
        now = datetime.now(tz=timezone.utc)

        if response.error or response.status_code >= 400:
            error_msg = response.error or f"HTTP {response.status_code}"
            return PageResult(
                url=url,
                status_code=response.status_code,
                depth=depth,
                parent_url=parent_url,
                error=error_msg,
                crawled_at=now,
            )

        body = response.body
        raw_links = extract_links(body)
        resolved: list[str] = []
        for href in raw_links:
            abs_url = resolve_url(url, href)
            if abs_url:
                resolved.append(normalize_url(abs_url))

        return PageResult(
            url=url,
            status_code=response.status_code,
            depth=depth,
            parent_url=parent_url,
            title=self._extract_title(body),
            links=resolved,
            forms=extract_forms(body, url),
            buttons=extract_buttons(body),
            api_endpoints=extract_api_endpoints(body),
            crawled_at=now,
        )

    @staticmethod
    def _extract_title(html: str) -> str | None:
        """Extract the <title> text from HTML.

        Args:
            html: Raw HTML content.

        Returns:
            Title string or None if not found.
        """
        match = _TITLE_RE.search(html)
        return match.group(1).strip() if match else None
