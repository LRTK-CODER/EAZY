"""Unit tests for NetworkInterceptor (TDD RED phase).

This test suite defines behavior for a NetworkInterceptor class that captures
XHR/fetch API requests during Playwright page navigation. Tests use MagicMock
to simulate Playwright Page and Request objects (sync, not async).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from eazy.crawler.network_interceptor import NetworkInterceptor
from eazy.models.crawl_types import EndpointInfo


def _make_request(
    url: str, method: str = "GET", resource_type: str = "xhr"
) -> MagicMock:
    """Create a mock Playwright Request with given properties.

    Args:
        url: Request URL.
        method: HTTP method.
        resource_type: Playwright resource type (xhr, fetch, stylesheet, etc).

    Returns:
        MagicMock with url, method, and resource_type attributes.
    """
    req = MagicMock()
    req.url = url
    req.method = method
    req.resource_type = resource_type
    return req


def _make_page() -> tuple[MagicMock, dict[str, list]]:
    """Create a mock Playwright Page that captures event handlers.

    Returns:
        Tuple of (page mock, dict mapping event names to handler lists).
    """
    page = MagicMock()
    handlers: dict[str, list] = {}

    def mock_on(event: str, handler):
        handlers.setdefault(event, []).append(handler)

    page.on = MagicMock(side_effect=mock_on)
    page.remove_listener = MagicMock()
    return page, handlers


class TestNetworkInterceptor:
    """Test XHR/fetch API request capture via NetworkInterceptor."""

    def test_capture_xhr_requests_returns_endpoint_info(self) -> None:
        """Fire xhr request and verify EndpointInfo with source='xhr'."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)

        # Act
        handlers["request"][0](
            _make_request("https://api.example.com/users", resource_type="xhr")
        )
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 1
        assert isinstance(endpoints[0], EndpointInfo)
        assert endpoints[0].source == "xhr"

    def test_capture_fetch_requests_returns_endpoint_info(self) -> None:
        """Fire fetch request and verify EndpointInfo with source='fetch'."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)

        # Act
        handlers["request"][0](
            _make_request("https://api.example.com/data", resource_type="fetch")
        )
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 1
        assert endpoints[0].source == "fetch"

    def test_capture_ignores_static_resources(self) -> None:
        """Fire stylesheet/image/font/script requests and get empty results."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)
        handler = handlers["request"][0]

        # Act
        handler(
            _make_request(
                "https://example.com/style.css",
                resource_type="stylesheet",
            )
        )
        handler(_make_request("https://example.com/logo.png", resource_type="image"))
        handler(_make_request("https://example.com/font.woff", resource_type="font"))
        handler(_make_request("https://example.com/app.js", resource_type="script"))
        endpoints = interceptor.get_endpoints()

        # Assert
        assert endpoints == []

    def test_capture_includes_request_method(self) -> None:
        """Fire POST request and verify method='POST' in EndpointInfo."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)

        # Act
        handlers["request"][0](
            _make_request(
                "https://api.example.com/submit",
                method="POST",
                resource_type="xhr",
            )
        )
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 1
        assert endpoints[0].method == "POST"

    def test_capture_includes_request_url(self) -> None:
        """Fire request with specific URL and verify url matches."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)
        target_url = "https://api.example.com/v2/users?page=1"

        # Act
        handlers["request"][0](_make_request(target_url, resource_type="fetch"))
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 1
        assert endpoints[0].url == target_url

    def test_capture_deduplicates_identical_api_calls(self) -> None:
        """Fire same (url, method) twice and get only 1 result."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)
        handler = handlers["request"][0]

        # Act
        handler(_make_request("https://api.example.com/users", resource_type="xhr"))
        handler(_make_request("https://api.example.com/users", resource_type="xhr"))
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 1

    def test_start_capture_before_navigation_captures_initial_requests(
        self,
    ) -> None:
        """Start interceptor, fire requests, and verify get_endpoints returns them."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)
        handler = handlers["request"][0]

        # Act
        handler(_make_request("https://api.example.com/init", resource_type="xhr"))
        handler(_make_request("https://api.example.com/config", resource_type="fetch"))
        endpoints = interceptor.get_endpoints()

        # Assert
        assert len(endpoints) == 2
        urls = {ep.url for ep in endpoints}
        assert "https://api.example.com/init" in urls
        assert "https://api.example.com/config" in urls

    def test_stop_capture_returns_collected_endpoints(self) -> None:
        """Start, fire, stop: returns list and removes listener."""
        # Arrange
        interceptor = NetworkInterceptor()
        page, handlers = _make_page()
        interceptor.start(page)
        handler = handlers["request"][0]

        # Act
        handler(_make_request("https://api.example.com/users", resource_type="xhr"))
        handler(_make_request("https://api.example.com/posts", resource_type="fetch"))
        result = interceptor.stop()

        # Assert
        assert len(result) == 2
        assert all(isinstance(ep, EndpointInfo) for ep in result)
        page.remove_listener.assert_called_once()
