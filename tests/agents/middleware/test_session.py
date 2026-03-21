"""Tests for session middleware — cookie/JWT/CSRF management + scope boundary."""

import base64
import json
import time
from unittest.mock import AsyncMock

import httpx
import pytest

from src.agents.middleware.session import (
    CookieManager,
    CSRFManager,
    JWTManager,
    ScopeBoundary,
    SessionMiddleware,
)


def _make_jwt(exp: int, header: dict[str, str] | None = None) -> str:
    """Create a minimal JWT with the given exp claim (no signature)."""
    hdr = header or {"alg": "none", "typ": "JWT"}
    payload = {"sub": "user", "exp": exp}
    h = base64.urlsafe_b64encode(json.dumps(hdr).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}.fakesig"


# ---------------------------------------------------------------------------
# CookieManager (5 tests)
# ---------------------------------------------------------------------------
class TestCookieManager:
    def test_cookie_extract_from_response(self) -> None:
        mgr = CookieManager()
        response = httpx.Response(
            200,
            headers=[("set-cookie", "sid=abc123; Path=/")],
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_cookies(response)
        assert mgr.get("sid") == "abc123"

    def test_cookie_inject_to_request(self) -> None:
        mgr = CookieManager()
        response = httpx.Response(
            200,
            headers=[("set-cookie", "sid=abc123; Path=/")],
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_cookies(response)
        request = httpx.Request("GET", "http://example.com/api")
        updated = mgr.inject_cookies(request)
        assert "sid=abc123" in updated.headers.get("cookie", "")

    def test_cookie_expired_not_injected(self) -> None:
        mgr = CookieManager()
        response = httpx.Response(
            200,
            headers=[("set-cookie", "old=stale; Max-Age=0")],
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_cookies(response)
        request = httpx.Request("GET", "http://example.com/api")
        updated = mgr.inject_cookies(request)
        assert "old" not in updated.headers.get("cookie", "")

    def test_cookie_multiple_cookies(self) -> None:
        mgr = CookieManager()
        response = httpx.Response(
            200,
            headers=[
                ("set-cookie", "a=1; Path=/"),
                ("set-cookie", "b=2; Path=/"),
            ],
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_cookies(response)
        request = httpx.Request("GET", "http://example.com/api")
        updated = mgr.inject_cookies(request)
        cookie_header = updated.headers.get("cookie", "")
        assert "a=1" in cookie_header
        assert "b=2" in cookie_header

    def test_cookie_clear(self) -> None:
        mgr = CookieManager()
        response = httpx.Response(
            200,
            headers=[("set-cookie", "sid=abc123; Path=/")],
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_cookies(response)
        mgr.clear()
        request = httpx.Request("GET", "http://example.com/api")
        updated = mgr.inject_cookies(request)
        assert updated.headers.get("cookie", "") == ""


# ---------------------------------------------------------------------------
# JWTManager (5 tests)
# ---------------------------------------------------------------------------
class TestJWTManager:
    def test_jwt_not_expired(self) -> None:
        mgr = JWTManager()
        token = _make_jwt(exp=int(time.time()) + 3600)
        mgr.set_tokens(access_token=token)
        assert mgr.is_expired() is False

    def test_jwt_expired(self) -> None:
        mgr = JWTManager()
        token = _make_jwt(exp=int(time.time()) - 3600)
        mgr.set_tokens(access_token=token)
        assert mgr.is_expired() is True

    def test_jwt_auth_header(self) -> None:
        mgr = JWTManager()
        token = _make_jwt(exp=int(time.time()) + 3600)
        mgr.set_tokens(access_token=token)
        header = mgr.get_auth_header()
        assert header == {"Authorization": f"Bearer {token}"}

    async def test_jwt_refresh(self) -> None:
        mgr = JWTManager()
        old_token = _make_jwt(exp=int(time.time()) - 10)
        new_token = _make_jwt(exp=int(time.time()) + 3600)
        mgr.set_tokens(access_token=old_token, refresh_token="refresh-xyz")

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = httpx.Response(
            200,
            json={"access_token": new_token},
            request=httpx.Request("POST", "http://example.com/refresh"),
        )
        await mgr.refresh(client=mock_client, refresh_url="http://example.com/refresh")
        assert mgr.get_auth_header() == {"Authorization": f"Bearer {new_token}"}

    async def test_jwt_no_refresh_token(self) -> None:
        mgr = JWTManager()
        token = _make_jwt(exp=int(time.time()) - 10)
        mgr.set_tokens(access_token=token)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        with pytest.raises(ValueError, match="refresh"):
            await mgr.refresh(
                client=mock_client, refresh_url="http://example.com/refresh"
            )


# ---------------------------------------------------------------------------
# CSRFManager (4 tests)
# ---------------------------------------------------------------------------
class TestCSRFManager:
    def test_csrf_extract_from_body(self) -> None:
        mgr = CSRFManager()
        response = httpx.Response(
            200,
            json={"csrf_token": "tok-body-123"},
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_token(response)
        assert mgr.token == "tok-body-123"

    def test_csrf_extract_from_header(self) -> None:
        mgr = CSRFManager()
        response = httpx.Response(
            200,
            headers={"X-CSRF-Token": "tok-header-456"},
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_token(response)
        assert mgr.token == "tok-header-456"

    def test_csrf_inject_to_request(self) -> None:
        mgr = CSRFManager()
        response = httpx.Response(
            200,
            headers={"X-CSRF-Token": "tok-inject"},
            request=httpx.Request("GET", "http://example.com"),
        )
        mgr.extract_token(response)
        request = httpx.Request("POST", "http://example.com/api")
        updated = mgr.inject_token(request)
        assert updated.headers["x-csrf-token"] == "tok-inject"

    def test_csrf_no_token(self) -> None:
        mgr = CSRFManager()
        request = httpx.Request("POST", "http://example.com/api")
        updated = mgr.inject_token(request)
        assert "x-csrf-token" not in updated.headers


# ---------------------------------------------------------------------------
# ScopeBoundary (4 tests)
# ---------------------------------------------------------------------------
class TestScopeBoundary:
    def test_scope_exact_match(self) -> None:
        boundary = ScopeBoundary(scope=["example.com"])
        assert boundary.is_in_scope("http://example.com/api") is True

    def test_scope_wildcard(self) -> None:
        boundary = ScopeBoundary(scope=["*.example.com"])
        assert boundary.is_in_scope("http://sub.example.com") is True

    def test_scope_out_of_scope(self) -> None:
        boundary = ScopeBoundary(scope=["example.com"])
        assert boundary.is_in_scope("http://other.com") is False

    def test_scope_exclude(self) -> None:
        boundary = ScopeBoundary(scope=["example.com"], exclude=["example.com"])
        assert boundary.is_in_scope("http://example.com/api") is False


# ---------------------------------------------------------------------------
# SessionMiddleware integration (3 tests)
# ---------------------------------------------------------------------------
class TestSessionMiddleware:
    async def test_middleware_cookie_flow(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mw = SessionMiddleware(client=mock_client, scope=["example.com"])
        # First response sets a cookie
        mock_client.send.return_value = httpx.Response(
            200,
            headers=[("set-cookie", "sid=flow123; Path=/")],
            request=httpx.Request("GET", "http://example.com/login"),
        )
        await mw.request("GET", "http://example.com/login")

        # Second request should carry the cookie
        mock_client.send.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "http://example.com/api"),
        )
        await mw.request("GET", "http://example.com/api")

        second_call_request = mock_client.send.call_args_list[1][0][0]
        assert "sid=flow123" in second_call_request.headers.get("cookie", "")

    async def test_middleware_scope_rejection(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mw = SessionMiddleware(client=mock_client, scope=["example.com"])
        with pytest.raises(ValueError, match="scope"):
            await mw.request("GET", "http://evil.com/steal")

    async def test_middleware_csrf_flow(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mw = SessionMiddleware(client=mock_client, scope=["example.com"])
        # First response provides CSRF token
        mock_client.send.return_value = httpx.Response(
            200,
            headers={"X-CSRF-Token": "csrf-flow-789"},
            request=httpx.Request("GET", "http://example.com/form"),
        )
        await mw.request("GET", "http://example.com/form")

        # Second request should carry the CSRF token
        mock_client.send.return_value = httpx.Response(
            200,
            request=httpx.Request("POST", "http://example.com/submit"),
        )
        await mw.request("POST", "http://example.com/submit")

        second_call_request = mock_client.send.call_args_list[1][0][0]
        assert second_call_request.headers.get("x-csrf-token") == "csrf-flow-789"
