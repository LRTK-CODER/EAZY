"""Tests for AuthenticatedCrawler — 인증 크롤링."""

import json
from typing import Any

import httpx
import pytest

from src.agents.core.models import CryptoContext, Endpoint
from src.agents.middleware.session import ScopeBoundary
from src.agents.recon.crawler import (
    ApiCallRelation,
    AuthenticatedCrawler,
    CrawlResult,
    DataFlowPath,
)


class _MockLLMClient:
    """Mock LLM client — tracks call count, optional failure."""

    def __init__(self, response: str, *, should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0

    async def interpret(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("LLM unavailable")
        return self.response


def _make_response(
    status: int,
    *,
    body: str = "",
    headers: list[tuple[str, str]] | None = None,
    url: str = "http://example.com/",
) -> httpx.Response:
    """Build an httpx.Response for testing."""
    kwargs: dict[str, Any] = {
        "status_code": status,
        "request": httpx.Request("GET", url),
        "text": body,
    }
    if headers:
        kwargs["headers"] = headers
    return httpx.Response(**kwargs)


class _MockSessionMiddleware:
    """Mock SessionMiddleware — records requests, returns canned responses."""

    def __init__(
        self,
        responses: list[httpx.Response],
        scope: list[str] | None = None,
    ) -> None:
        self._responses = responses
        self._index = 0
        self.scope = ScopeBoundary(scope=scope or ["example.com"])
        self.request_log: list[tuple[str, str]] = []

    async def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        if not self.scope.is_in_scope(url):
            msg = f"URL out of scope: {url}"
            raise ValueError(msg)
        self.request_log.append((method, url))
        resp = self._responses[self._index % len(self._responses)]
        self._index += 1
        return resp


class TestAuthenticatedCrawler:
    """Tests for AuthenticatedCrawler."""

    @pytest.mark.asyncio()
    async def test_crawl_returns_crawl_result(self) -> None:
        """crawl() returns a CrawlResult instance."""
        session = _MockSessionMiddleware(
            responses=[_make_response(200, body="<html></html>")],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/")

        assert isinstance(result, CrawlResult)

    @pytest.mark.asyncio()
    async def test_crawl_discovers_endpoints(self) -> None:
        """Endpoints are extracted from HTML links and forms."""
        html = (
            "<html><body>"
            '<a href="/api/users">Users</a>'
            '<form action="/api/login" method="POST">'
            '<input name="user"/></form>'
            "</body></html>"
        )
        session = _MockSessionMiddleware(
            responses=[_make_response(200, body=html)],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/")

        assert len(result.discovered_endpoints) >= 2
        assert all(isinstance(e, Endpoint) for e in result.discovered_endpoints)

    @pytest.mark.asyncio()
    async def test_crawl_extracts_api_call_relations(self) -> None:
        """API call relations are extracted from JS fetch calls."""
        html = (
            "<html><body>"
            '<script>fetch("/api/orders", {method: "GET"})</script>'
            "</body></html>"
        )
        session = _MockSessionMiddleware(
            responses=[_make_response(200, body=html)],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/dashboard")

        assert len(result.api_calls) >= 1
        rel = result.api_calls[0]
        assert isinstance(rel, ApiCallRelation)
        assert "/api/orders" in rel.target_url
        assert "dashboard" in rel.source_url

    @pytest.mark.asyncio()
    async def test_crawl_tracks_data_flow(self) -> None:
        """Data flow is tracked when a parameter appears across endpoints."""
        page1_html = (
            "<html><body>"
            '<a href="http://example.com/profile?user_id=42">Profile</a>'
            "</body></html>"
        )
        page2_html = (
            "<html><body>"
            '<form action="/api/update" method="POST">'
            '<input name="user_id" value="42"/>'
            "</form></body></html>"
        )
        session = _MockSessionMiddleware(
            responses=[
                _make_response(200, body=page1_html, url="http://example.com/home"),
                _make_response(
                    200,
                    body=page2_html,
                    url="http://example.com/profile",
                ),
            ],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/home", max_depth=2)

        assert len(result.data_flows) >= 1
        flow = result.data_flows[0]
        assert isinstance(flow, DataFlowPath)
        assert flow.param_name == "user_id"

    @pytest.mark.asyncio()
    async def test_crawl_respects_max_depth(self) -> None:
        """Crawl stops at max_depth and does not visit deeper pages."""

        def _link_page(depth: int) -> str:
            next_url = f"http://example.com/level{depth + 1}"
            return f'<html><a href="{next_url}">Next</a></html>'

        responses = [
            _make_response(
                200,
                body=_link_page(i),
                url=f"http://example.com/level{i}",
            )
            for i in range(6)
        ]
        session = _MockSessionMiddleware(responses=responses)
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/level0", max_depth=2)

        # depth 0, 1, 2 → at most 3 pages
        assert len(result.pages_visited) <= 3
        deep_urls = [u for u in result.pages_visited if "level3" in u or "level4" in u]
        assert deep_urls == []

    @pytest.mark.asyncio()
    async def test_crawl_respects_scope_boundary(self) -> None:
        """Out-of-scope URLs are not visited."""
        html = (
            "<html><body>"
            '<a href="http://evil.com/steal">Evil</a>'
            '<a href="http://example.com/safe">Safe</a>'
            "</body></html>"
        )
        session = _MockSessionMiddleware(
            responses=[
                _make_response(200, body=html),
                _make_response(200, body="<html></html>"),
            ],
            scope=["example.com"],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/")

        visited_hosts = [u for u in result.pages_visited if "evil.com" in u]
        assert visited_hosts == []
        logged_hosts = [u for _, u in session.request_log if "evil.com" in u]
        assert logged_hosts == []

    @pytest.mark.asyncio()
    async def test_crawl_extracts_crypto_params_from_js(self) -> None:
        """Crypto contexts are extracted from JavaScript."""
        html = (
            "<html><script>"
            "var encrypted = CryptoJS.AES.encrypt(data, 'key123');"
            "</script></html>"
        )
        session = _MockSessionMiddleware(
            responses=[_make_response(200, body=html)],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        result = await crawler.crawl("http://example.com/")

        assert len(result.crypto_contexts) >= 1
        ctx = result.crypto_contexts[0]
        assert isinstance(ctx, CryptoContext)
        assert ctx.detected is True
        assert ctx.algorithm is not None
        assert "AES" in ctx.algorithm

    @pytest.mark.asyncio()
    async def test_crawl_uses_authenticated_session(self) -> None:
        """All HTTP requests go through the session middleware."""
        html = '<html><a href="http://example.com/page2">Link</a></html>'
        session = _MockSessionMiddleware(
            responses=[
                _make_response(200, body=html),
                _make_response(200, body="<html></html>"),
            ],
        )
        llm = _MockLLMClient(response="[]")
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        await crawler.crawl("http://example.com/")

        assert len(session.request_log) >= 1
        assert all(method == "GET" for method, _ in session.request_log)

    @pytest.mark.asyncio()
    async def test_crawl_delegates_priority_to_llm(self) -> None:
        """LLM is called at least once to prioritize URLs."""
        html = (
            "<html><body>"
            '<a href="http://example.com/a">A</a>'
            '<a href="http://example.com/b">B</a>'
            "</body></html>"
        )
        session = _MockSessionMiddleware(
            responses=[
                _make_response(200, body=html),
                _make_response(200, body="<html></html>"),
                _make_response(200, body="<html></html>"),
            ],
        )
        llm = _MockLLMClient(
            response=json.dumps(["http://example.com/a", "http://example.com/b"]),
        )
        crawler = AuthenticatedCrawler(session=session, llm_client=llm)  # type: ignore[arg-type]

        await crawler.crawl("http://example.com/")

        assert llm.call_count >= 1
