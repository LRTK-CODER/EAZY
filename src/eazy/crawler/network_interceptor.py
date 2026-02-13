"""Network interceptor for capturing XHR/fetch API requests during navigation.

This module provides the NetworkInterceptor class that hooks into Playwright's
request events to capture API endpoint calls made by the browser, filtering
out static resources like stylesheets, images, fonts, and scripts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, ClassVar

from eazy.models.crawl_types import EndpointInfo

if TYPE_CHECKING:
    from playwright.async_api import Page, Request

__all__ = ["NetworkInterceptor"]


class NetworkInterceptor:
    """Capture XHR/fetch API requests during Playwright page navigation.

    Registers a request listener on a Playwright Page to intercept network
    requests, filtering for API calls (xhr/fetch) and deduplicating by
    (url, method) pair.

    Example:
        interceptor = NetworkInterceptor()
        interceptor.start(page)
        await page.goto("https://example.com")
        endpoints = interceptor.stop()
    """

    _API_RESOURCE_TYPES: ClassVar[frozenset[str]] = frozenset({"xhr", "fetch"})

    def __init__(self) -> None:
        """Initialize empty interceptor state."""
        self._endpoints: list[EndpointInfo] = []
        self._seen: set[tuple[str, str]] = set()
        self._handler: Callable[[Request], None] | None = None
        self._page: Page | None = None

    def start(self, page: Page) -> None:
        """Register request listener on the page.

        Args:
            page: Playwright Page object to listen on.
        """
        self._page = page
        self._handler = self._on_request
        page.on("request", self._handler)

    def stop(self) -> list[EndpointInfo]:
        """Remove listener and return captured endpoints.

        Returns:
            List of captured EndpointInfo objects.
        """
        if self._page and self._handler:
            self._page.remove_listener("request", self._handler)
        result = list(self._endpoints)
        self._handler = None
        self._page = None
        return result

    def get_endpoints(self) -> list[EndpointInfo]:
        """Return snapshot of currently captured endpoints.

        Returns:
            Copy of the captured EndpointInfo list.
        """
        return list(self._endpoints)

    def _on_request(self, request: Request) -> None:
        """Filter and capture API requests.

        Args:
            request: Playwright Request object from the event.
        """
        if request.resource_type not in self._API_RESOURCE_TYPES:
            return
        key = (request.url, request.method)
        if key in self._seen:
            return
        self._seen.add(key)
        self._endpoints.append(
            EndpointInfo(
                url=request.url,
                method=request.method,
                source=request.resource_type,
            )
        )
