"""OAuth 2.0 authorization code flow infrastructure."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from eazy.ai.models import LLMError, OAuthConfig, OAuthTokens


class OAuthCallbackServer:
    """Minimal HTTP server to receive OAuth authorization codes.

    Listens on a local port for a single GET request containing
    the authorization code as a query parameter.

    Attributes:
        _host: Bind address.
        _port: Requested port (0 for OS-assigned).
        _timeout: Max seconds to wait for callback.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 0,
        timeout: float = 120,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._server: asyncio.Server | None = None
        self._code_future: asyncio.Future[str] | None = None

    async def start(self) -> int:
        """Start the callback server.

        Returns:
            The actual port the server is listening on.
        """
        loop = asyncio.get_running_loop()
        self._code_future = loop.create_future()
        self._server = await asyncio.start_server(self._handle, self._host, self._port)
        return self._server.sockets[0].getsockname()[1]

    async def wait_for_code(self) -> str:
        """Wait for the authorization code callback.

        Returns:
            The authorization code string.

        Raises:
            LLMError: If the callback times out.
        """
        try:
            return await asyncio.wait_for(self._code_future, timeout=self._timeout)
        except asyncio.TimeoutError:
            raise LLMError("OAuth callback timeout") from None
        finally:
            if self._server:
                self._server.close()

    async def _handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle incoming HTTP request."""
        line = await reader.readline()
        parts = line.decode().strip().split(" ")
        code = None
        if len(parts) >= 2:
            parsed = urlparse(parts[1])
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]

        body = (
            "<html><body>Authorization successful. "
            "You can close this window.</body></html>"
        )
        header = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Content-Type: text/html\r\n"
            "\r\n"
        )
        writer.write((header + body).encode())
        await writer.drain()
        writer.close()

        if code and self._code_future and not self._code_future.done():
            self._code_future.set_result(code)


class OAuthFlow:
    """OAuth 2.0 authorization code flow.

    Builds auth URLs, exchanges codes for tokens,
    and refreshes expired tokens.

    Attributes:
        _config: OAuth configuration.
        _client: Optional shared httpx client.
    """

    def __init__(
        self,
        config: OAuthConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._client = client

    def build_auth_url(self, redirect_uri: str) -> str:
        """Build the authorization URL.

        Args:
            redirect_uri: Local callback URI.

        Returns:
            Full authorization URL with query parameters.
        """
        params = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._config.scopes),
        }
        return f"{self._config.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokens:
        """Exchange an authorization code for tokens.

        Args:
            code: Authorization code from callback.
            redirect_uri: Must match the one used in auth URL.

        Returns:
            OAuth tokens with access, refresh, and expiry.

        Raises:
            LLMError: If the token endpoint returns an error.
        """
        form = {
            "code": code,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        return await self._token_request(form)

    async def refresh_token(self, refresh_token: str) -> OAuthTokens:
        """Refresh an access token.

        Args:
            refresh_token: The refresh token to use.

        Returns:
            New OAuth tokens.

        Raises:
            LLMError: If the token endpoint returns an error.
        """
        form = {
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "grant_type": "refresh_token",
        }
        return await self._token_request(form, fallback_refresh=refresh_token)

    async def _token_request(
        self,
        form: dict[str, str],
        fallback_refresh: str | None = None,
    ) -> OAuthTokens:
        """Send a token request to the token endpoint.

        Args:
            form: Form data for the POST request.
            fallback_refresh: Refresh token to use if not
                returned in the response.

        Returns:
            Parsed OAuth tokens.

        Raises:
            LLMError: On non-200 response.
        """
        client = self._client or httpx.AsyncClient()
        try:
            resp = await client.post(self._config.token_url, data=form)
            if resp.status_code != 200:
                msg = f"Token request failed: {resp.text}"
                raise LLMError(msg)
            body = resp.json()
            expires_at = int(time.time() * 1000 + body["expires_in"] * 1000)
            return OAuthTokens(
                access_token=body["access_token"],
                refresh_token=body.get(
                    "refresh_token",
                    fallback_refresh or "",
                ),
                expires_at=expires_at,
            )
        finally:
            if not self._client:
                await client.aclose()
