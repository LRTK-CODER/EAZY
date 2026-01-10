import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_crawler_uses_explicit_timeout():
    """Test that crawler uses explicit timeout for page.goto()."""
    from app.services.crawler_service import CrawlerService

    with patch('app.services.crawler_service.async_playwright') as mock_playwright:
        # Setup mocks
        mock_page = AsyncMock()
        mock_page.locator.return_value.all.return_value = []

        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context

        mock_pw = AsyncMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_pw

        crawler = CrawlerService()
        await crawler.crawl("https://example.com")

        # Verify timeout parameter is passed
        mock_page.goto.assert_called_once()
        call_kwargs = mock_page.goto.call_args[1]
        assert "timeout" in call_kwargs, "timeout parameter should be passed to page.goto()"
        assert call_kwargs["timeout"] == 30000, "timeout should be 30000ms (30 seconds)"
