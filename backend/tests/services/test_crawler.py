import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crawler_service import CrawlerService

@pytest.mark.asyncio
async def test_crawl_page_extracts_links():
    """Test that crawler extracts links from a page."""
    
    # Mock data
    mock_elements = [AsyncMock(), AsyncMock()]
    mock_elements[0].get_attribute.return_value = "https://example.com/page1"
    mock_elements[1].get_attribute.return_value = "/about"
    
    # Patch async_playwright context manager
    with patch("app.services.crawler_service.async_playwright") as mock_playwright_ctx:
        mock_context_manager = AsyncMock()
        mock_playwright_ctx.return_value = mock_context_manager
        
        mock_p = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_p
        
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        # Setup page.locator("a").all() return
        # page.locator is SYNC, so use MagicMock
        mock_locator = AsyncMock()
        mock_locator.all.return_value = mock_elements
        
        mock_page.locator = MagicMock(return_value=mock_locator)

        
        # Run Code
        crawler = CrawlerService()
        links = await crawler.crawl("https://example.com")
        
        # Verify
        assert "https://example.com/page1" in links
        assert "/about" in links
        assert len(links) == 2
        
        mock_page.goto.assert_called_with("https://example.com", wait_until="networkidle")
