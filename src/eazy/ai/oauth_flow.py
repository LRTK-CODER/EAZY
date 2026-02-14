"""OAuth 2.0 authorization flow engine for LLM provider authentication."""

from __future__ import annotations

import asyncio
import secrets
import webbrowser
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from eazy.ai.models import OAuthTokens
from eazy.ai.oauth_callback import OAuthCallbackServer


class OAuthError(Exception):
    """Raised when an OAuth operation fails."""


class OAuthFlowEngine:
    """OAuth 2.0 authorization code flow engine.

    Handles authorization URL generation, code-to-token exchange,
    and token refresh operations for LLM provider authentication.

    Args:
        client_id: OAuth client identifier.
        client_secret: OAuth client secret.
        auth_url: Authorization endpoint URL.
        token_url: Token exchange endpoint URL.
        scopes: List of OAuth scopes to request.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_url: str,
        token_url: str,
        scopes: list[str],
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_url = auth_url
        self._token_url = token_url
        self._scopes = scopes

    def generate_auth_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Build OAuth authorization URL with required parameters.

        Args:
            redirect_uri: URI to redirect to after authorization.
            state: CSRF protection state parameter.

        Returns:
            Complete authorization URL with query parameters.
        """
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._scopes),
        }
        if state is not None:
            params["state"] = state

        query_string = urlencode(params)
        return f"{self._auth_url}?{query_string}"

    def generate_state(self) -> str:
        """Generate a cryptographically random state parameter.

        Returns:
            URL-safe random string for CSRF protection.
        """
        return secrets.token_urlsafe(32)

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokens:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback.
            redirect_uri: Same redirect_uri used in authorization.

        Returns:
            OAuth tokens including access and refresh tokens.

        Raises:
            OAuthError: If token exchange fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )

            if not response.is_success:
                raise OAuthError(f"Token exchange failed: {response.status_code}")

            data = response.json()
            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=data["expires_in"]
                )

            return OAuthTokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_at=expires_at,
                scope=data.get("scope", ""),
            )

    async def refresh_token(self, refresh_token: str) -> OAuthTokens:
        """Refresh an expired access token.

        Args:
            refresh_token: Refresh token from previous authorization.

        Returns:
            New OAuth tokens with fresh access token.

        Raises:
            OAuthError: If token refresh fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )

            if not response.is_success:
                raise OAuthError(f"Token refresh failed: {response.status_code}")

            data = response.json()
            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=data["expires_in"]
                )

            return OAuthTokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_at=expires_at,
                scope=data.get("scope", ""),
            )

    @staticmethod
    def is_token_expired(expires_at: datetime | None) -> bool:
        """Check if a token has expired.

        Args:
            expires_at: Token expiration time (UTC). None means expired.

        Returns:
            True if expired or no expiry set, False if still valid.
        """
        if expires_at is None:
            return True
        return datetime.now(timezone.utc) >= expires_at

    async def run_interactive_flow(
        self,
        redirect_host: str = "localhost",
        redirect_port: int = 0,
        timeout: float = 120.0,
    ) -> OAuthTokens:
        """Run the full interactive OAuth browser flow.

        Starts a local callback server, opens the browser for user
        consent, waits for the authorization callback, verifies the
        state parameter, and exchanges the code for tokens.

        Args:
            redirect_host: Hostname for the callback server.
            redirect_port: Port for callback (0 = auto-assign).
            timeout: Max seconds to wait for user consent.

        Returns:
            OAuthTokens from successful authentication.

        Raises:
            OAuthError: On state mismatch, timeout, or exchange
                failure.
        """
        async with OAuthCallbackServer(
            host=redirect_host, port=redirect_port
        ) as server:
            redirect_uri = f"http://{redirect_host}:{server.port}/callback"
            state = self.generate_state()
            auth_url = self.generate_auth_url(redirect_uri, state)

            webbrowser.open(auth_url)

            try:
                code, received_state = await server.wait_for_callback(timeout=timeout)
            except asyncio.TimeoutError:
                raise OAuthError("OAuth flow timed out waiting for callback.")

            if received_state != state:
                raise OAuthError("State mismatch: possible CSRF attack.")

            return await self.exchange_code(code, redirect_uri)
