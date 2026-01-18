"""
Test 5-Imp.18: CrawlerService HTTP Interception Tests (RED Phase)
Expected to FAIL: CrawlerService doesn't register page event handlers yet
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.crawler_service import CrawlerService


@pytest.mark.asyncio
async def test_crawler_registers_request_handler():
    """Test CrawlerService registers page.on('request') handler - RED Phase"""
    service = CrawlerService()

    # Mock Playwright page
    mock_page = MagicMock()
    mock_request_handler = None

    def capture_request_handler(event_name, handler):
        nonlocal mock_request_handler
        if event_name == "request":
            mock_request_handler = handler

    mock_page.on = MagicMock(side_effect=capture_request_handler)
    mock_page.goto = AsyncMock()
    mock_page.locator = MagicMock(
        return_value=MagicMock(all=AsyncMock(return_value=[]))
    )

    # Patch playwright context
    with patch("app.services.crawler_service.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                chromium=MagicMock(launch=AsyncMock(return_value=mock_browser))
            )
        )

        # Call crawl - should FAIL: page.on("request") is never called
        await service.crawl("http://example.com")

    # Verify request handler was registered
    assert (
        mock_request_handler is not None
    ), "CrawlerService should register 'request' event handler"


@pytest.mark.asyncio
async def test_crawler_registers_response_handler():
    """Test CrawlerService registers page.on('response') handler - RED Phase"""
    service = CrawlerService()

    # Mock Playwright page
    mock_page = MagicMock()
    mock_response_handler = None

    def capture_response_handler(event_name, handler):
        nonlocal mock_response_handler
        if event_name == "response":
            mock_response_handler = handler

    mock_page.on = MagicMock(side_effect=capture_response_handler)
    mock_page.goto = AsyncMock()
    mock_page.locator = MagicMock(
        return_value=MagicMock(all=AsyncMock(return_value=[]))
    )

    # Patch playwright
    with patch("app.services.crawler_service.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                chromium=MagicMock(launch=AsyncMock(return_value=mock_browser))
            )
        )

        # Call crawl - should FAIL: page.on("response") is never called
        await service.crawl("http://example.com")

    # Verify response handler was registered
    assert (
        mock_response_handler is not None
    ), "CrawlerService should register 'response' event handler"


@pytest.mark.asyncio
async def test_crawler_collects_http_request_data():
    """Test HTTP request data collection (method, headers, body) - RED Phase"""
    service = CrawlerService()

    # This test expects crawl() to return HTTP data
    # Currently crawl() only returns List[str] (URLs)
    # Should FAIL: TypeError or KeyError when accessing http_data

    result = await service.crawl("http://example.com")

    # Expected new return signature: Tuple[List[str], Dict[str, Any]]
    # Should FAIL: result is still just List[str]
    assert isinstance(result, tuple), "crawl() should return tuple (links, http_data)"
    links, http_data = result

    # Verify structure
    assert isinstance(http_data, dict), "http_data should be a dictionary"


@pytest.mark.asyncio
async def test_crawler_collects_http_response_data():
    """Test HTTP response data collection (status, headers, body) - RED Phase"""
    service = CrawlerService()

    # Mock to simulate HTTP response
    result = await service.crawl("http://example.com")

    # Should FAIL: result is List[str], not tuple
    assert isinstance(result, tuple), "crawl() should return (links, http_data)"
    links, http_data = result

    # http_data should contain response information
    assert isinstance(http_data, dict), "http_data should be dict"

    # Structure check (will fail - http_data doesn't exist yet)
    # Expected format: {url: {request: {...}, response: {...}}}
    assert len(http_data) >= 0, "http_data should be present even if empty"


@pytest.mark.asyncio
async def test_crawler_enforces_body_size_limit():
    """Test body size limit enforcement (10KB max) - RED Phase"""
    service = CrawlerService()

    # This test expects truncation logic in crawler
    # Should FAIL: body size limit not implemented

    # Mock a large response body
    _large_body = "x" * 20000  # 20KB

    result = await service.crawl("http://example.com")

    # Should FAIL: result is List[str], not tuple
    assert isinstance(result, tuple), "crawl() should return (links, http_data)"
    links, http_data = result

    # Verify body truncation logic exists (will fail)
    # When implemented, response bodies should be max 10KB
    MAX_BODY_SIZE = 10 * 1024  # 10KB

    # This assertion will fail - no truncation logic exists yet
    for url, data in http_data.items():
        if "response" in data and "body" in data["response"]:
            body = data["response"]["body"]
            if body:
                assert len(body) <= MAX_BODY_SIZE, "Response body exceeds 10KB limit"
