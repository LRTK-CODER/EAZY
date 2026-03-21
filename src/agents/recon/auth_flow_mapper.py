"""AuthFlowMapper — 인증 흐름 자동 매핑."""

from __future__ import annotations

import contextlib
import json
from typing import Any

import httpx
from pydantic import BaseModel, Field

from src.agents.core.models import AuthFlow, AuthStep
from src.agents.recon.scan_interpreter import LLMClient


class Credentials(BaseModel):
    """Login credentials for authentication flow mapping."""

    username: str
    password: str
    extra_fields: dict[str, str] = Field(default_factory=dict)


class AuthFlowResult(BaseModel):
    """Structured result of authentication flow mapping."""

    auth_flow: AuthFlow
    success: bool
    login_url: str
    redirect_chain: list[str] = Field(default_factory=list)
    raw_responses: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    is_fallback: bool = False


class AuthFlowMapper:
    """Maps authentication flows by executing login and analyzing responses.

    Performs login attempt, tracks redirects, and uses a single LLM call
    to interpret the authentication mechanism (cookie/jwt/bearer/custom),
    2FA presence, and SSO usage.
    """

    MAX_STEPS: int = 10

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        llm_client: LLMClient,
    ) -> None:
        self._http_client = http_client
        self._llm_client = llm_client

    async def map_auth_flow(
        self,
        target_url: str,
        credentials: Credentials,
    ) -> AuthFlowResult:
        """Map authentication flow for the given target URL."""
        redirect_chain: list[str] = []
        raw_responses: list[dict[str, Any]] = []

        try:
            # Step 1: GET login page
            get_resp = await self._http_client.request("GET", target_url)
            raw_responses.append(_serialize_response(get_resp))

            # Step 2: POST credentials
            post_data = {
                "username": credentials.username,
                "password": credentials.password,
                **credentials.extra_fields,
            }
            post_resp = await self._http_client.request(
                "POST",
                target_url,
                json=post_data,
            )
            raw_responses.append(_serialize_response(post_resp))

            # Step 3: Follow redirect chain manually
            current_resp = post_resp
            for _ in range(self.MAX_STEPS):
                if current_resp.status_code not in {301, 302, 303, 307, 308}:
                    break
                location = current_resp.headers.get("location", "")
                if not location:
                    break
                redirect_chain.append(location)
                current_resp = await self._http_client.request("GET", location)
                raw_responses.append(_serialize_response(current_resp))

            # Step 4: LLM interprets collected data (exactly 1 call)
            prompt = _build_interpret_prompt(raw_responses, redirect_chain)
            llm_response = await self._llm_client.interpret(prompt)
            return _parse_llm_auth_response(
                llm_response,
                redirect_chain,
                raw_responses,
                target_url,
            )
        except Exception:  # noqa: BLE001
            return _build_fallback(redirect_chain, raw_responses, target_url)


def _build_interpret_prompt(
    raw_responses: list[dict[str, Any]],
    redirect_chain: list[str],
) -> str:
    """Build LLM prompt for auth flow interpretation."""
    serialized = json.dumps(
        {"responses": raw_responses, "redirect_chain": redirect_chain},
        indent=2,
    )
    return (
        "You are a security analyst. Analyze the following authentication "
        "flow data and return a JSON object with these fields:\n"
        "- session_mechanism: one of 'cookie', 'jwt', 'bearer', 'custom'\n"
        "- two_factor: boolean\n"
        "- sso: boolean\n"
        "- steps: list of objects with order (int ≥1), action (str), "
        "description (str)\n"
        "- login_success: boolean\n"
        "- error_reason: string or null\n\n"
        "Return ONLY valid JSON, no markdown.\n\n"
        f"Auth Flow Data:\n{serialized}"
    )


def _parse_llm_auth_response(
    response: str,
    redirect_chain: list[str],
    raw_responses: list[dict[str, Any]],
    login_url: str,
) -> AuthFlowResult:
    """Parse LLM JSON response into AuthFlowResult."""
    data = json.loads(response)

    steps = [AuthStep(**s) for s in data.get("steps", [])]
    auth_flow = AuthFlow(
        steps=steps,
        session_mechanism=data.get("session_mechanism", "custom"),
        two_factor=data.get("two_factor", False),
        sso=data.get("sso", False),
    )

    login_success = data.get("login_success", True)
    error_reason = data.get("error_reason")

    return AuthFlowResult(
        auth_flow=auth_flow,
        success=login_success,
        login_url=login_url,
        redirect_chain=redirect_chain,
        raw_responses=raw_responses,
        error=error_reason,
        is_fallback=False,
    )


def _build_fallback(
    redirect_chain: list[str],
    raw_responses: list[dict[str, Any]],
    login_url: str,
) -> AuthFlowResult:
    """Build fallback result when LLM call fails."""
    return AuthFlowResult(
        auth_flow=AuthFlow(
            steps=[],
            session_mechanism="custom",
        ),
        success=False,
        login_url=login_url,
        redirect_chain=redirect_chain,
        raw_responses=raw_responses,
        error="LLM interpretation failed — raw responses attached",
        is_fallback=True,
    )


def _serialize_response(response: httpx.Response) -> dict[str, Any]:
    """Serialize an httpx.Response to a JSON-safe dict."""
    body: str | None = None
    with contextlib.suppress(Exception):
        body = response.text

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "url": str(response.request.url),
        "body": body,
    }
