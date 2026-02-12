"""Unit tests for HTTP client module."""

from unittest.mock import AsyncMock, patch

import httpx
import respx
from eazy.crawler.http_client import HttpClient

from eazy.models.crawl_types import CrawlConfig


class TestHttpClient:
    """Test suite for HttpClient."""

    @respx.mock
    async def test_fetch_success_returns_html(self) -> None:
        """Test fetch returns HTML body on successful 200 response."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com")
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200,
                text="<html>OK</html>",
                headers={"content-type": "text/html"},
            )
        )

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/")

        # Assert
        assert response.status_code == 200
        assert response.body == "<html>OK</html>"
        assert response.error is None
        assert response.url == "https://example.com/"

    @respx.mock
    async def test_fetch_404_returns_error_status(self) -> None:
        """Test fetch returns 404 status without error (4xx is not an error state)."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com")
        respx.get("https://example.com/missing").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/missing")

        # Assert
        assert response.status_code == 404
        assert response.error is None
        assert len(respx.calls) == 1  # No retries on 4xx

    @respx.mock
    async def test_fetch_timeout_returns_error(self) -> None:
        """Test fetch returns error on timeout."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com", max_retries=0)
        respx.get("https://example.com/slow").mock(side_effect=httpx.ReadTimeout(""))

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/slow")

        # Assert
        assert response.status_code == 0
        assert response.error is not None
        assert "timed out" in response.error.lower()

    @respx.mock
    async def test_fetch_follows_redirects(self) -> None:
        """Test fetch follows redirects and returns final URL."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com")
        respx.get("https://example.com/old").mock(
            return_value=httpx.Response(
                301,
                headers={"Location": "https://example.com/new"},
            )
        )
        respx.get("https://example.com/new").mock(
            return_value=httpx.Response(200, text="<html>New page</html>")
        )

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/old")

        # Assert
        assert response.status_code == 200
        assert response.url == "https://example.com/new"
        assert response.body == "<html>New page</html>"

    @respx.mock
    async def test_fetch_connection_error_returns_error(self) -> None:
        """Test fetch returns error on connection failure."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com", max_retries=0)
        respx.get("https://example.com/").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/")

        # Assert
        assert response.status_code == 0
        assert response.error is not None
        assert "connect" in response.error.lower()

    @respx.mock
    async def test_fetch_retries_on_server_error(self) -> None:
        """Test fetch retries on 5xx server errors."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com", max_retries=3)
        respx.get("https://example.com/").mock(
            side_effect=[
                httpx.Response(503, text="Service Unavailable"),
                httpx.Response(503, text="Service Unavailable"),
                httpx.Response(200, text="<html>OK</html>"),
            ]
        )

        # Act
        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/")

        # Assert
        assert response.status_code == 200
        assert len(respx.calls) == 3

    @patch("asyncio.sleep", new_callable=AsyncMock)
    @respx.mock
    async def test_fetch_respects_request_delay(self, mock_sleep: AsyncMock) -> None:
        """Test fetch waits request_delay between consecutive requests."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com", request_delay=1.0)
        respx.get("https://example.com/page1").mock(
            return_value=httpx.Response(200, text="<html>Page 1</html>")
        )
        respx.get("https://example.com/page2").mock(
            return_value=httpx.Response(200, text="<html>Page 2</html>")
        )

        # Act
        async with HttpClient(config) as client:
            await client.fetch("https://example.com/page1")
            await client.fetch("https://example.com/page2")

        # Assert
        # Sleep should be called once before second fetch with delay=1.0
        mock_sleep.assert_called_once()
        call_args = mock_sleep.call_args[0][0]
        assert abs(call_args - 1.0) < 0.01

    @respx.mock
    async def test_fetch_sends_custom_user_agent(self) -> None:
        """Test fetch sends custom User-Agent header from config."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com", user_agent="TestBot/1.0")
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(200, text="<html>OK</html>")
        )

        # Act
        async with HttpClient(config) as client:
            await client.fetch("https://example.com/")

        # Assert
        assert len(respx.calls) == 1
        request_headers = respx.calls[0].request.headers
        assert request_headers.get("user-agent") == "TestBot/1.0"
