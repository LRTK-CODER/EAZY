"""Manage Playwright browser lifecycle for smart crawling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page, Playwright

from eazy.models.crawl_types import CrawlConfig

__all__ = ["BrowserManager"]


class BrowserManager:
    """Manage Playwright browser lifecycle for smart crawling.

    Provides an async context manager that launches a Chromium browser
    and creates pages with the configured viewport and user agent.

    Args:
        config: Crawl configuration with browser settings.

    Example:
        async with BrowserManager(config) as bm:
            page = await bm.new_page()
            await page.goto("https://example.com")
    """

    def __init__(self, config: CrawlConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def __aenter__(self) -> BrowserManager:
        """Launch the browser and return self."""
        await self.launch()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Close the browser and stop Playwright."""
        await self.close()

    async def launch(self) -> None:
        """Start Playwright and launch Chromium browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._config.headless,
        )

    async def new_page(self) -> Page:
        """Create a new page with configured viewport and user agent.

        Returns:
            A new Playwright Page instance.

        Raises:
            RuntimeError: If the browser has not been launched.
        """
        if self._browser is None:
            raise RuntimeError(
                "Browser not launched. "
                "Use 'async with BrowserManager(config)' "
                "or call launch() first."
            )
        context = await self._browser.new_context(
            viewport={
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            },
            user_agent=self._config.user_agent,
        )
        return await context.new_page()

    async def close(self) -> None:
        """Close the browser and stop Playwright.

        Safe to call multiple times. Silently ignores if
        browser or Playwright is already closed or None.
        """
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
