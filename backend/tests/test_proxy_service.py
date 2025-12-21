import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.proxy_service import ProxyService

@pytest.mark.asyncio
async def test_launch_browser():
    service = ProxyService()
    
    # Mock Playwright
    with patch("app.services.proxy_service.async_playwright") as mock_pw:
        mock_context_manager = AsyncMock()
        mock_pw.return_value = mock_context_manager
        
        mock_playwright_obj = AsyncMock()
        mock_context_manager.start.return_value = mock_playwright_obj
        
        mock_browser = AsyncMock()
        mock_playwright_obj.chromium.launch.return_value = mock_browser
        
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        # Test Launch
        target_url = "http://example.com"
        await service.launch_browser(target_url, 8081)
        
        # Verify calls
        mock_playwright_obj.chromium.launch.assert_called_once()
        assert mock_playwright_obj.chromium.launch.call_args[1]['headless'] == False
        assert mock_playwright_obj.chromium.launch.call_args[1]['proxy']['server'] == "http://localhost:8081"
        
        mock_page.goto.assert_called_once_with(target_url)
        
        # Cleanup
        await service.stop_browser()
        mock_browser.close.assert_called_once()
        mock_playwright_obj.stop.assert_called_once()

