"""Async HTTP client with retry, delay, and error handling."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Self

import httpx

from eazy.models.crawl_types import CrawlConfig


@dataclass(frozen=True)
class HttpResponse:
    """Low-level HTTP response container.

    Attributes:
        url: Final URL after redirects.
        status_code: HTTP status code. 0 on transport-level failure.
        body: Response body text.
        headers: Response headers as a dict.
        error: Error message if the request failed, None on success.
    """

    url: str
    status_code: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)
    error: str | None = None


class HttpClient:
    """Async HTTP client wrapping httpx.AsyncClient.

    Provides retry logic for 5xx/timeout/connect errors, per-request delay,
    and custom User-Agent header. Use as an async context manager.

    Args:
        config: Crawl configuration with timeout, retry, delay settings.

    Example::

        async with HttpClient(config) as client:
            response = await client.fetch("https://example.com/")
    """

    def __init__(self, config: CrawlConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0.0

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.timeout),
            follow_redirects=True,
            headers={"User-Agent": self._config.user_agent},
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str) -> HttpResponse:
        """Fetch a URL with retry and delay logic.

        Args:
            url: The URL to fetch.

        Returns:
            HttpResponse with status, body, headers, and optional error.
        """
        assert self._client is not None, (
            "HttpClient must be used as async context manager"
        )

        await self._wait_for_delay()

        last_error: str | None = None
        max_attempts = self._config.max_retries + 1

        for attempt in range(max_attempts):
            try:
                resp = await self._client.get(url)

                if resp.status_code >= 500 and attempt < max_attempts - 1:
                    continue

                return HttpResponse(
                    url=str(resp.url),
                    status_code=resp.status_code,
                    body=resp.text,
                    headers=dict(resp.headers),
                )

            except httpx.TimeoutException:
                last_error = "Request timed out"
                if attempt < max_attempts - 1:
                    continue
            except httpx.ConnectError:
                last_error = "Connection failed"
                if attempt < max_attempts - 1:
                    continue

        return HttpResponse(
            url=url,
            status_code=0,
            body="",
            error=last_error,
        )

    async def _wait_for_delay(self) -> None:
        """Wait for request_delay seconds since the last request."""
        if self._config.request_delay > 0 and self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            remaining = self._config.request_delay - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)

        self._last_request_time = time.monotonic()
