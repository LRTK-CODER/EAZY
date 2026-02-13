"""Unit tests for BrowserManager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eazy.crawler.browser_manager import BrowserManager
from eazy.models.crawl_types import CrawlConfig


@pytest.fixture
def config():
    """Default CrawlConfig for tests."""
    return CrawlConfig(target_url="https://example.com")


@pytest.fixture
def custom_config():
    """Custom CrawlConfig with non-default smart crawling fields."""
    return CrawlConfig(
        target_url="https://example.com",
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
        user_agent="CustomBot/2.0",
    )


def _make_playwright_mock():
    """Create a fully mocked Playwright instance."""
    page_mock = AsyncMock()
    context_mock = AsyncMock()
    context_mock.new_page = AsyncMock(return_value=page_mock)
    browser_mock = AsyncMock()
    browser_mock.new_context = AsyncMock(return_value=context_mock)
    browser_mock.is_connected = MagicMock(return_value=True)
    playwright_mock = AsyncMock()
    playwright_mock.chromium = AsyncMock()
    playwright_mock.chromium.launch = AsyncMock(return_value=browser_mock)
    return playwright_mock, browser_mock, context_mock, page_mock


class TestBrowserManager:
    """Tests for BrowserManager lifecycle and page creation."""

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_async_context_manager_starts_browser(self, mock_ap):
        """BrowserManager should launch browser on __aenter__."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(target_url="https://example.com")

        async with BrowserManager(config) as bm:
            pw.chromium.launch.assert_called_once()
            assert bm._browser is browser

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_async_context_manager_closes_on_exit(self, mock_ap):
        """BrowserManager should close browser on __aexit__."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(target_url="https://example.com")

        async with BrowserManager(config):
            pass

        browser.close.assert_called_once()
        pw.stop.assert_called_once()

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_closes_browser_on_exception(self, mock_ap):
        """BrowserManager should close browser even if exception."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(target_url="https://example.com")

        with pytest.raises(RuntimeError, match="test error"):
            async with BrowserManager(config):
                raise RuntimeError("test error")

        browser.close.assert_called_once()
        pw.stop.assert_called_once()

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_creates_page_with_viewport(self, mock_ap):
        """new_page should create context with configured viewport."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(
            target_url="https://example.com",
            viewport_width=1920,
            viewport_height=1080,
        )

        async with BrowserManager(config) as bm:
            result = await bm.new_page()

        browser.new_context.assert_called_once()
        call_kwargs = browser.new_context.call_args[1]
        assert call_kwargs["viewport"] == {
            "width": 1920,
            "height": 1080,
        }
        assert result is page

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_sets_user_agent(self, mock_ap):
        """new_page should set user_agent from config."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(
            target_url="https://example.com",
            user_agent="CustomBot/2.0",
        )

        async with BrowserManager(config) as bm:
            await bm.new_page()

        call_kwargs = browser.new_context.call_args[1]
        assert call_kwargs["user_agent"] == "CustomBot/2.0"

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_headless_mode(self, mock_ap):
        """BrowserManager should pass headless config to launch."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(
            target_url="https://example.com",
            headless=False,
        )

        async with BrowserManager(config):
            pass

        call_kwargs = pw.chromium.launch.call_args[1]
        assert call_kwargs["headless"] is False

    @patch("eazy.crawler.browser_manager.async_playwright")
    async def test_reuses_browser_across_pages(self, mock_ap):
        """Multiple new_page calls should reuse the same browser."""
        pw, browser, context, page = _make_playwright_mock()
        mock_ap.return_value.start = AsyncMock(return_value=pw)
        config = CrawlConfig(target_url="https://example.com")

        async with BrowserManager(config) as bm:
            await bm.new_page()
            await bm.new_page()

        # Browser launched only once
        pw.chromium.launch.assert_called_once()
        # But new_context called twice (one per page)
        assert browser.new_context.call_count == 2
