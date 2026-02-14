"""Unit tests for OAuthCallbackServer.

Test Coverage:
- Server starts and binds to a port
- Receives authorization code and state from callback
- Returns success HTML response
- Timeout when no callback received
- Handles missing code parameter with 400 response
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from eazy.ai.oauth_callback import OAuthCallbackServer


class TestOAuthCallbackServer:
    """Test suite for OAuth callback server."""

    async def test_callback_server_starts_and_binds_port(self):
        """start() binds to an available port > 0."""
        # Arrange & Act
        async with OAuthCallbackServer() as server:
            # Assert
            assert server.port > 0

    async def test_callback_server_receives_code_and_state(self):
        """GET /callback?code=X&state=Y returns (X, Y)."""
        # Arrange
        async with OAuthCallbackServer() as server:
            # Act — simulate browser redirect
            async with httpx.AsyncClient() as client:
                await client.get(
                    f"http://localhost:{server.port}"
                    "/callback?code=test_code&state=test_state"
                )

            code, state = await server.wait_for_callback(timeout=2.0)

            # Assert
            assert code == "test_code"
            assert state == "test_state"

    async def test_callback_server_returns_success_html(self):
        """GET /callback with code returns 200 with success message."""
        # Arrange
        async with OAuthCallbackServer() as server:
            # Act
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"http://localhost:{server.port}/callback?code=abc&state=xyz"
                )

            # Assert
            assert resp.status_code == 200
            assert "Authentication successful" in resp.text

    async def test_callback_server_timeout_on_no_callback(self):
        """wait_for_callback() raises TimeoutError when no request."""
        # Arrange
        async with OAuthCallbackServer() as server:
            # Act & Assert
            with pytest.raises(asyncio.TimeoutError):
                await server.wait_for_callback(timeout=0.1)

    async def test_callback_server_handles_missing_code(self):
        """GET /callback without code returns 400 response."""
        # Arrange
        async with OAuthCallbackServer() as server:
            # Act
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"http://localhost:{server.port}/callback?state=only_state"
                )

            # Assert
            assert resp.status_code == 400
