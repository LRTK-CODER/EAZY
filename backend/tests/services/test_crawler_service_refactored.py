"""Tests for CrawlerService refactoring with ResponseParserRegistry.

TDD RED Phase: These tests verify that CrawlerService properly delegates
content parsing to the ResponseParserRegistry and its registered parsers.
"""

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.crawler_service import CrawlerService
from app.services.parsers import (
    ResponseParserRegistry,
    JsonResponseParser,
    HtmlResponseParser,
    ImageResponseParser,
)


class TestCrawlerServiceParserRegistry:
    """Test CrawlerService integration with ResponseParserRegistry."""

    @pytest.mark.asyncio
    async def test_crawler_uses_parser_registry(self) -> None:
        """CrawlerService should accept and use an injected parser registry."""
        # Arrange
        mock_registry = MagicMock(spec=ResponseParserRegistry)
        mock_parser = MagicMock()
        mock_parser.parse = AsyncMock(
            return_value={
                "content_type": "application/json",
                "body": '{"key": "value"}',
                "truncated": False,
                "original_size": 16,
            }
        )
        mock_registry.get_parser.return_value = mock_parser

        # Act - CrawlerService should accept parser_registry
        service = CrawlerService(parser_registry=mock_registry)

        # Mock Playwright
        with patch("app.services.crawler_service.async_playwright") as mock_playwright:
            mock_page = MagicMock()
            mock_response_handler = None

            def capture_handler(event_name: str, handler) -> None:
                nonlocal mock_response_handler
                if event_name == "response":
                    mock_response_handler = handler

            mock_page.on = MagicMock(side_effect=capture_handler)
            mock_page.goto = AsyncMock()
            mock_page.locator = MagicMock(
                return_value=MagicMock(all=AsyncMock(return_value=[]))
            )

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_p = MagicMock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_p)
            mock_playwright.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.crawl("http://example.com")

            # Simulate a response to trigger the handler
            if mock_response_handler:
                mock_response = AsyncMock()
                mock_response.url = "http://example.com/api"
                mock_response.status = 200
                mock_response.headers = {"content-type": "application/json"}
                mock_response.body = AsyncMock(return_value=b'{"key": "value"}')

                await mock_response_handler(mock_response)

        # Assert - registry was used
        assert (
            mock_registry.get_parser.called
        ), "CrawlerService should call registry.get_parser()"

    @pytest.mark.asyncio
    async def test_crawler_delegates_to_json_parser(self) -> None:
        """CrawlerService should delegate JSON parsing to JsonResponseParser."""
        # Arrange - Create registry with JSON parser
        registry = ResponseParserRegistry()
        registry.register(JsonResponseParser())

        service = CrawlerService(parser_registry=registry)

        with patch("app.services.crawler_service.async_playwright") as mock_playwright:
            mock_page = MagicMock()
            captured_handler = None

            def capture_handler(event_name: str, handler) -> None:
                nonlocal captured_handler
                if event_name == "response":
                    captured_handler = handler

            mock_page.on = MagicMock(side_effect=capture_handler)
            mock_page.goto = AsyncMock()
            mock_page.locator = MagicMock(
                return_value=MagicMock(all=AsyncMock(return_value=[]))
            )

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_p = MagicMock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_p)
            mock_playwright.return_value.__aexit__ = AsyncMock(return_value=None)

            links, http_data = await service.crawl("http://example.com")

            # Simulate JSON response
            assert captured_handler is not None
            mock_response = AsyncMock()
            mock_response.url = "http://example.com/api/data"
            mock_response.status = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.body = AsyncMock(return_value=b'{"test": "value"}')

            await captured_handler(mock_response)

        # Assert - JSON was parsed correctly
        assert "http://example.com/api/data" in http_data
        response_data = http_data["http://example.com/api/data"]["response"]
        assert response_data["body"] is not None
        assert "test" in response_data["body"]

    @pytest.mark.asyncio
    async def test_crawler_delegates_to_html_parser(self) -> None:
        """CrawlerService should delegate HTML parsing to HtmlResponseParser."""
        # Arrange
        registry = ResponseParserRegistry()
        registry.register(HtmlResponseParser())

        service = CrawlerService(parser_registry=registry)

        with patch("app.services.crawler_service.async_playwright") as mock_playwright:
            mock_page = MagicMock()
            captured_handler = None

            def capture_handler(event_name: str, handler) -> None:
                nonlocal captured_handler
                if event_name == "response":
                    captured_handler = handler

            mock_page.on = MagicMock(side_effect=capture_handler)
            mock_page.goto = AsyncMock()
            mock_page.locator = MagicMock(
                return_value=MagicMock(all=AsyncMock(return_value=[]))
            )

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_p = MagicMock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_p)
            mock_playwright.return_value.__aexit__ = AsyncMock(return_value=None)

            links, http_data = await service.crawl("http://example.com")

            # Simulate HTML response
            assert captured_handler is not None
            mock_response = AsyncMock()
            mock_response.url = "http://example.com/page.html"
            mock_response.status = 200
            mock_response.headers = {"content-type": "text/html; charset=utf-8"}
            mock_response.body = AsyncMock(
                return_value=b"<html><body>Hello</body></html>"
            )

            await captured_handler(mock_response)

        # Assert
        assert "http://example.com/page.html" in http_data
        response_data = http_data["http://example.com/page.html"]["response"]
        assert "<html>" in response_data["body"]

    @pytest.mark.asyncio
    async def test_crawler_delegates_to_image_parser(self) -> None:
        """CrawlerService should delegate image parsing to ImageResponseParser."""
        # Arrange
        registry = ResponseParserRegistry()
        registry.register(ImageResponseParser())

        service = CrawlerService(parser_registry=registry)

        with patch("app.services.crawler_service.async_playwright") as mock_playwright:
            mock_page = MagicMock()
            captured_handler = None

            def capture_handler(event_name: str, handler) -> None:
                nonlocal captured_handler
                if event_name == "response":
                    captured_handler = handler

            mock_page.on = MagicMock(side_effect=capture_handler)
            mock_page.goto = AsyncMock()
            mock_page.locator = MagicMock(
                return_value=MagicMock(all=AsyncMock(return_value=[]))
            )

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_p = MagicMock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_p)
            mock_playwright.return_value.__aexit__ = AsyncMock(return_value=None)

            links, http_data = await service.crawl("http://example.com")

            # Simulate image response
            image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00"
            assert captured_handler is not None
            mock_response = AsyncMock()
            mock_response.url = "http://example.com/image.png"
            mock_response.status = 200
            mock_response.headers = {"content-type": "image/png"}
            mock_response.body = AsyncMock(return_value=image_bytes)

            await captured_handler(mock_response)

        # Assert - Body should be base64 encoded
        assert "http://example.com/image.png" in http_data
        response_data = http_data["http://example.com/image.png"]["response"]
        expected_base64 = base64.b64encode(image_bytes).decode("ascii")
        assert response_data["body"] == expected_base64

    @pytest.mark.asyncio
    async def test_crawler_uses_default_for_unknown(self) -> None:
        """CrawlerService should use DefaultResponseParser for unknown content types."""
        # Arrange - Empty registry (will use DefaultResponseParser as fallback)
        registry = ResponseParserRegistry()

        service = CrawlerService(parser_registry=registry)

        with patch("app.services.crawler_service.async_playwright") as mock_playwright:
            mock_page = MagicMock()
            captured_handler = None

            def capture_handler(event_name: str, handler) -> None:
                nonlocal captured_handler
                if event_name == "response":
                    captured_handler = handler

            mock_page.on = MagicMock(side_effect=capture_handler)
            mock_page.goto = AsyncMock()
            mock_page.locator = MagicMock(
                return_value=MagicMock(all=AsyncMock(return_value=[]))
            )

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_p = MagicMock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_p)
            mock_playwright.return_value.__aexit__ = AsyncMock(return_value=None)

            links, http_data = await service.crawl("http://example.com")

            # Simulate unknown content type response
            assert captured_handler is not None
            mock_response = AsyncMock()
            mock_response.url = "http://example.com/file.xyz"
            mock_response.status = 200
            mock_response.headers = {"content-type": "application/octet-stream"}
            mock_response.body = AsyncMock(return_value=b"\x00\x01\x02\x03")

            await captured_handler(mock_response)

        # Assert - DefaultResponseParser returns None for body
        assert "http://example.com/file.xyz" in http_data
        response_data = http_data["http://example.com/file.xyz"]["response"]
        assert response_data["body"] is None

    @pytest.mark.asyncio
    async def test_crawler_creates_default_registry_if_none_provided(self) -> None:
        """CrawlerService should create a default registry with all parsers if none provided."""
        # Act - No parser_registry argument
        service = CrawlerService()

        # Assert - Should have a registry with standard parsers
        assert hasattr(service, "_parser_registry")
        assert service._parser_registry is not None

        # Verify it handles JSON correctly (default registry should include JsonResponseParser)
        parser = service._parser_registry.get_parser("application/json")
        assert parser is not None

        # Verify it handles HTML correctly
        parser = service._parser_registry.get_parser("text/html")
        assert parser is not None

        # Verify it handles images correctly
        parser = service._parser_registry.get_parser("image/png")
        assert parser is not None
