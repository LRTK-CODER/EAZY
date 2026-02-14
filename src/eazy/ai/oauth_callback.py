"""Local OAuth callback server using pure asyncio.

Receives the authorization code from the OAuth provider's redirect
without any external HTTP framework dependencies.
"""

from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

_SUCCESS_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Connection: close\r\n"
    "\r\n"
    "<!DOCTYPE html>\n"
    "<html><body>\n"
    "<h1>Authentication successful</h1>\n"
    "<p>You can close this tab and return to the terminal.</p>\n"
    "</body></html>"
)

_ERROR_RESPONSE = (
    "HTTP/1.1 400 Bad Request\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Connection: close\r\n"
    "\r\n"
    "<!DOCTYPE html>\n"
    "<html><body>\n"
    "<h1>Authentication failed</h1>\n"
    "<p>Missing authorization code parameter.</p>\n"
    "</body></html>"
)


class OAuthCallbackServer:
    """Local HTTP server to receive OAuth authorization callbacks.

    Uses pure asyncio (no external dependencies). Listens for a single
    GET /callback request containing 'code' and 'state' query
    parameters.

    Args:
        host: Hostname to bind to.
        port: Port to bind to. 0 for OS auto-assignment.
    """

    def __init__(self, host: str = "localhost", port: int = 0) -> None:
        self._host = host
        self._port = port
        self._server: asyncio.Server | None = None
        self._auth_code: str | None = None
        self._received_state: str | None = None
        self._code_received = asyncio.Event()

    @property
    def port(self) -> int:
        """Actual port after server starts."""
        return self._port

    async def start(self) -> None:
        """Start the callback server."""
        self._server = await asyncio.start_server(
            self._handle_request,
            self._host,
            self._port,
        )
        sock = self._server.sockets[0]
        self._port = sock.getsockname()[1]

    async def wait_for_callback(self, timeout: float = 120.0) -> tuple[str, str]:
        """Wait for OAuth callback with code and state.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            Tuple of (authorization_code, state).

        Raises:
            asyncio.TimeoutError: If no callback within timeout.
        """
        await asyncio.wait_for(self._code_received.wait(), timeout=timeout)
        return self._auth_code, self._received_state  # type: ignore[return-value]

    async def stop(self) -> None:
        """Stop the server and release resources."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def __aenter__(self) -> OAuthCallbackServer:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Parse HTTP GET and extract code/state from query."""
        data = await reader.read(4096)
        request_line = data.split(b"\r\n")[0].decode()
        # "GET /callback?code=xxx&state=yyy HTTP/1.1"
        path = request_line.split(" ")[1]
        parsed = urlparse(path)
        params = parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if code:
            self._auth_code = code
            self._received_state = state
            writer.write(_SUCCESS_RESPONSE.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            self._code_received.set()
        else:
            writer.write(_ERROR_RESPONSE.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
