"""Tests for AuthFlowMapper — 인증 흐름 자동 매핑."""

import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from src.agents.recon.auth_flow_mapper import (
    AuthFlowMapper,
    AuthFlowResult,
    Credentials,
)


class _MockLLMClient:
    """Mock LLM client for testing — only external boundary is mocked."""

    def __init__(self, response: str, *, should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0

    async def interpret(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("LLM unavailable")
        return self.response


def _build_auth_llm_response(
    *,
    session_mechanism: str = "cookie",
    two_factor: bool = False,
    sso: bool = False,
    steps: list[dict[str, Any]] | None = None,
    login_success: bool = True,
    error_reason: str | None = None,
) -> str:
    """Build a parameterized LLM JSON response for auth flow interpretation."""
    if steps is None:
        steps = [
            {"order": 1, "action": "GET /login", "description": "Load login page"},
            {"order": 2, "action": "POST /login", "description": "Submit credentials"},
        ]
    return json.dumps(
        {
            "session_mechanism": session_mechanism,
            "two_factor": two_factor,
            "sso": sso,
            "steps": steps,
            "login_success": login_success,
            "error_reason": error_reason,
        }
    )


def _make_response(
    status: int,
    *,
    headers: list[tuple[str, str]] | None = None,
    json_body: dict[str, Any] | None = None,
    url: str = "http://example.com/login",
) -> httpx.Response:
    """Build an httpx.Response for testing."""
    kwargs: dict[str, Any] = {
        "status_code": status,
        "request": httpx.Request("POST", url),
    }
    if headers:
        kwargs["headers"] = headers
    if json_body is not None:
        kwargs["json"] = json_body
    return httpx.Response(**kwargs)


@pytest.fixture()
def credentials() -> Credentials:
    return Credentials(username="admin", password="secret123")


class TestAuthFlowMapper:
    """Tests for AuthFlowMapper."""

    @pytest.mark.asyncio()
    async def test_map_returns_auth_flow_result(self, credentials: Credentials) -> None:
        """map_auth_flow returns an AuthFlowResult instance."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(
            200,
            headers=[("set-cookie", "sid=abc; Path=/")],
            url="http://example.com/login",
        )
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(session_mechanism="cookie"),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert isinstance(result, AuthFlowResult)

    @pytest.mark.asyncio()
    async def test_map_identifies_cookie_session(
        self, credentials: Credentials
    ) -> None:
        """Cookie session mechanism is correctly identified."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(
            200,
            headers=[("set-cookie", "sid=abc; Path=/")],
        )
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(session_mechanism="cookie"),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert result.auth_flow.session_mechanism == "cookie"

    @pytest.mark.asyncio()
    async def test_map_identifies_jwt_session(self, credentials: Credentials) -> None:
        """JWT session mechanism is correctly identified."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(
            200,
            json_body={"access_token": "eyJhbGciOiJIUzI1NiJ9.test.sig"},
        )
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(session_mechanism="jwt"),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert result.auth_flow.session_mechanism == "jwt"

    @pytest.mark.asyncio()
    async def test_map_detects_2fa(self, credentials: Credentials) -> None:
        """Two-factor authentication is detected."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(
            200,
            json_body={"status": "otp_required", "2fa": True},
        )
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(two_factor=True),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert result.auth_flow.two_factor is True

    @pytest.mark.asyncio()
    async def test_map_follows_redirect_chain(self, credentials: Credentials) -> None:
        """Redirect chain is tracked across hops."""
        responses = [
            # GET login page
            _make_response(
                200,
                url="http://example.com/login",
            ),
            # POST login → 302
            _make_response(
                302,
                headers=[("location", "http://example.com/callback")],
                url="http://example.com/login",
            ),
            # Follow redirect → 302
            _make_response(
                302,
                headers=[("location", "http://example.com/dashboard")],
                url="http://example.com/callback",
            ),
            # Final destination → 200
            _make_response(
                200,
                headers=[("set-cookie", "sid=final; Path=/")],
                url="http://example.com/dashboard",
            ),
        ]
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.side_effect = responses
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(session_mechanism="cookie"),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert len(result.redirect_chain) >= 2

    @pytest.mark.asyncio()
    async def test_map_auth_failure_returns_result_not_error(
        self, credentials: Credentials
    ) -> None:
        """Authentication failure returns result with success=False, no exception."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(401)
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(login_success=False),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert result.success is False

    @pytest.mark.asyncio()
    async def test_map_delegates_to_llm_for_interpretation(
        self, credentials: Credentials
    ) -> None:
        """LLM is called exactly once for interpretation."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(200)
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        await mapper.map_auth_flow("http://example.com/login", credentials)

        assert mock_llm.call_count == 1

    @pytest.mark.asyncio()
    async def test_map_records_auth_steps_in_order(
        self, credentials: Credentials
    ) -> None:
        """Auth steps are recorded in correct order."""
        steps = [
            {"order": 1, "action": "GET /login", "description": "Load page"},
            {"order": 2, "action": "POST /login", "description": "Submit"},
            {"order": 3, "action": "GET /dashboard", "description": "Redirect"},
        ]
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.request.return_value = _make_response(200)
        mock_llm = _MockLLMClient(
            response=_build_auth_llm_response(steps=steps),
        )
        mapper = AuthFlowMapper(http_client=mock_http, llm_client=mock_llm)

        result = await mapper.map_auth_flow("http://example.com/login", credentials)

        assert len(result.auth_flow.steps) == 3
        for i, step in enumerate(result.auth_flow.steps):
            assert step.order == i + 1
