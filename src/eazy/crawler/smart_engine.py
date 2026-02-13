"""Playwright-based BFS smart crawler engine for JavaScript-rendered pages."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from eazy.crawler.browser_manager import BrowserManager
from eazy.crawler.graph_builder import GraphBuilder
from eazy.crawler.network_interceptor import NetworkInterceptor
from eazy.crawler.page_analyzer import PageAnalyzer
from eazy.crawler.robots_parser import RobotsParser
from eazy.crawler.sitemap import Sitemap
from eazy.crawler.url_pattern import URLPatternNormalizer
from eazy.crawler.url_resolver import is_in_scope, normalize_url
from eazy.models.crawl_types import CrawlConfig, CrawlResult, PageResult

if TYPE_CHECKING:
    from playwright.async_api import Page

__all__ = ["SmartCrawlerEngine"]


class SmartCrawlerEngine:
    """Playwright-based BFS crawling engine for JavaScript-rendered pages.

    Integrates BrowserManager, PageAnalyzer, and NetworkInterceptor
    to crawl SPA and dynamically rendered web pages. Reuses
    url_resolver, RobotsParser, URLPatternNormalizer, and Sitemap
    from the existing crawl modules.

    Args:
        config: Crawl configuration.
    """

    def __init__(self, config: CrawlConfig) -> None:
        self._config = config
        self._visited: set[str] = set()
        self._sitemap = Sitemap()
        self._robots: RobotsParser | None = None
        self._normalizer: URLPatternNormalizer | None = (
            URLPatternNormalizer(max_samples=config.max_samples_per_pattern)
            if config.enable_pattern_normalization
            else None
        )

    async def crawl(self) -> CrawlResult:
        """Run a BFS crawl using Playwright and return the result.

        Returns:
            CrawlResult with all discovered pages and statistics.
        """
        started_at = datetime.now(tz=timezone.utc)

        if self._config.respect_robots:
            await self._fetch_robots()

        async with BrowserManager(self._config) as browser:
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
                page_result = await self._crawl_page(browser, url, depth, parent_url)
                self._sitemap.add_page(page_result)
                if self._normalizer:
                    self._normalizer.add_url(url)

                if not page_result.error and page_result.status_code < 400:
                    for link in page_result.links:
                        normalized = normalize_url(link)
                        if normalized not in self._visited:
                            queue.append((normalized, depth + 1, url))

                if self._config.request_delay > 0:
                    await asyncio.sleep(self._config.request_delay)

        completed_at = datetime.now(tz=timezone.utc)
        result = CrawlResult(
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
        result.knowledge_graph = GraphBuilder.build(result)
        return result

    async def _crawl_page(
        self,
        browser: BrowserManager,
        url: str,
        depth: int,
        parent_url: str | None,
    ) -> PageResult:
        """Crawl a single page with Playwright.

        Args:
            browser: BrowserManager instance for creating pages.
            url: Normalized URL to crawl.
            depth: BFS depth from the root.
            parent_url: URL of the page that linked here.

        Returns:
            PageResult with extracted page structure.
        """
        now = datetime.now(tz=timezone.utc)
        page: Page | None = None
        interceptor = NetworkInterceptor()

        try:
            page = await browser.new_page()
            interceptor.start(page)

            response = await page.goto(
                url,
                wait_until=self._config.wait_until,
                timeout=self._config.timeout * 1000,
            )

            status_code = response.status if response else 0

            if status_code >= 400:
                endpoints = interceptor.stop()
                return PageResult(
                    url=url,
                    status_code=status_code,
                    depth=depth,
                    parent_url=parent_url,
                    error=f"HTTP {status_code}",
                    api_endpoints=endpoints,
                    crawled_at=now,
                )

            analyzer = PageAnalyzer(base_url=url)
            analysis = await analyzer.analyze(page)
            endpoints = interceptor.stop()

            return PageResult(
                url=url,
                status_code=status_code,
                depth=depth,
                parent_url=parent_url,
                title=analysis.title,
                links=analysis.links,
                forms=analysis.forms,
                buttons=analysis.buttons,
                api_endpoints=endpoints,
                crawled_at=now,
            )
        except Exception as exc:
            interceptor.stop()
            return PageResult(
                url=url,
                status_code=0,
                depth=depth,
                parent_url=parent_url,
                error=str(exc),
                crawled_at=now,
            )
        finally:
            if page is not None:
                await page.close()

    async def _fetch_robots(self) -> None:
        """Fetch and parse robots.txt from the target domain."""
        parsed = urlparse(self._config.target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(robots_url, timeout=self._config.timeout)
                body = resp.text if resp.status_code == 200 else ""
        except Exception:
            body = ""
        self._robots = RobotsParser(body)
