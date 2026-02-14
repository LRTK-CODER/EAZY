"""Unit tests for GeminiOAuthProvider.

Test Coverage:
- ABC compliance (LLMProvider)
- Capability properties (oauth, multi-account, billing)
- OAuth authentication flow
- Send request with Bearer token auth
- Auto-refresh expired tokens
- Token storage integration
- Endpoint URL verification
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from eazy.ai.exceptions import AuthenticationError
from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    OAuthTokens,
    ProviderType,
)
from eazy.ai.provider import LLMProvider
from eazy.ai.providers.gemini_oauth import GeminiOAuthProvider
from eazy.ai.token_storage import TokenStorage

CLOUDAICOMPANION_BASE = "https://cloudaicompanion.googleapis.com/v1beta"

MOCK_GEMINI_RESPONSE = {
    "candidates": [
        {
            "content": {"parts": [{"text": "Hello!"}]},
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 5,
        "candidatesTokenCount": 8,
        "totalTokenCount": 13,
    },
    "modelVersion": "gemini-2.0-flash",
}


def _make_valid_tokens(
    *,
    expired: bool = False,
) -> OAuthTokens:
    """Create OAuthTokens for testing."""
    if expired:
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return OAuthTokens(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=expires_at,
        scope="https://www.googleapis.com/auth/cloud-platform",
    )


def _make_refreshed_tokens() -> OAuthTokens:
    """Create fresh OAuthTokens as if just refreshed."""
    return OAuthTokens(
        access_token="refreshed-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="https://www.googleapis.com/auth/cloud-platform",
    )


class TestGeminiOAuthProvider:
    """Test suite for GeminiOAuthProvider."""

    def test_gemini_oauth_provider_implements_llm_provider(
        self,
        tmp_path: Path,
    ) -> None:
        """GeminiOAuthProvider is a subclass of LLMProvider ABC."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )

        # Act
        provider = GeminiOAuthProvider(token_storage=storage)

        # Assert
        assert isinstance(provider, LLMProvider)

    def test_gemini_oauth_provider_capability_oauth_supported(
        self,
        tmp_path: Path,
    ) -> None:
        """GeminiOAuthProvider supports OAuth."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = GeminiOAuthProvider(token_storage=storage)

        # Act & Assert
        assert provider.supports_oauth is True

    def test_gemini_oauth_provider_capability_multi_account(
        self,
        tmp_path: Path,
    ) -> None:
        """GeminiOAuthProvider supports multi-account."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = GeminiOAuthProvider(token_storage=storage)

        # Act & Assert
        assert provider.supports_multi_account is True

    def test_gemini_oauth_provider_billing_type_subscription(
        self,
        tmp_path: Path,
    ) -> None:
        """GeminiOAuthProvider uses subscription billing."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = GeminiOAuthProvider(token_storage=storage)

        # Act & Assert
        assert provider.billing_type == BillingType.SUBSCRIPTION

    async def test_gemini_oauth_provider_authenticate_triggers_oauth_flow(
        self,
        tmp_path: Path,
    ) -> None:
        """authenticate() calls OAuthFlowEngine.exchange_code."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        mock_engine = AsyncMock()
        mock_engine.exchange_code.return_value = _make_valid_tokens()

        provider = GeminiOAuthProvider(
            token_storage=storage,
            oauth_engine=mock_engine,
        )

        # Act
        result = await provider.authenticate(
            code="auth-code-123",
            redirect_uri="http://localhost:8080/callback",
            account_id="user@example.com",
        )

        # Assert
        assert result is True
        assert provider.is_authenticated is True
        mock_engine.exchange_code.assert_awaited_once_with(
            code="auth-code-123",
            redirect_uri="http://localhost:8080/callback",
        )

    @respx.mock
    async def test_gemini_oauth_provider_send_with_valid_token(
        self,
        tmp_path: Path,
    ) -> None:
        """send() with valid token uses Bearer auth header."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        mock_engine = AsyncMock()
        mock_engine.exchange_code.return_value = _make_valid_tokens()

        provider = GeminiOAuthProvider(
            token_storage=storage,
            oauth_engine=mock_engine,
        )
        await provider.authenticate(
            code="code",
            redirect_uri="http://localhost",
            account_id="user@example.com",
        )

        route = respx.post(
            url__startswith=f"{CLOUDAICOMPANION_BASE}/models/",
        ).mock(
            return_value=httpx.Response(
                200,
                json=MOCK_GEMINI_RESPONSE,
            ),
        )

        request = LLMRequest(prompt="Say hello")

        # Act
        response = await provider.send(request)

        # Assert
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello!"
        assert response.provider_type == ProviderType.GEMINI_OAUTH
        assert response.input_tokens == 5
        assert response.output_tokens == 8

        # Verify Bearer auth header
        sent_request = route.calls[0].request
        assert sent_request.headers["authorization"] == ("Bearer test-access-token")

    @respx.mock
    async def test_gemini_oauth_provider_auto_refreshes_expired_token(
        self,
        tmp_path: Path,
    ) -> None:
        """Expired token triggers refresh before send."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        mock_engine = AsyncMock()
        mock_engine.exchange_code.return_value = _make_valid_tokens(expired=True)
        mock_engine.refresh_token.return_value = _make_refreshed_tokens()

        provider = GeminiOAuthProvider(
            token_storage=storage,
            oauth_engine=mock_engine,
        )
        await provider.authenticate(
            code="code",
            redirect_uri="http://localhost",
            account_id="user@example.com",
        )

        route = respx.post(
            url__startswith=f"{CLOUDAICOMPANION_BASE}/models/",
        ).mock(
            return_value=httpx.Response(
                200,
                json=MOCK_GEMINI_RESPONSE,
            ),
        )

        request = LLMRequest(prompt="Say hello")

        # Act
        response = await provider.send(request)

        # Assert
        assert response.content == "Hello!"
        mock_engine.refresh_token.assert_awaited_once_with(
            "test-refresh-token",
        )
        # Should use refreshed token
        sent_request = route.calls[0].request
        assert sent_request.headers["authorization"] == (
            "Bearer refreshed-access-token"
        )

    async def test_gemini_oauth_provider_stores_token_via_token_storage(
        self,
        tmp_path: Path,
    ) -> None:
        """After authenticate, token is persisted in TokenStorage."""
        # Arrange
        key = Fernet.generate_key()
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=key,
        )
        mock_engine = AsyncMock()
        mock_engine.exchange_code.return_value = _make_valid_tokens()

        provider = GeminiOAuthProvider(
            token_storage=storage,
            oauth_engine=mock_engine,
        )

        # Act
        await provider.authenticate(
            code="code",
            redirect_uri="http://localhost",
            account_id="user@example.com",
        )

        # Assert — token file should exist
        loaded = storage.load("gemini_oauth", "user@example.com")
        assert loaded is not None
        assert loaded["access_token"] == "test-access-token"

    def test_gemini_oauth_provider_loads_existing_token_on_init(
        self,
        tmp_path: Path,
    ) -> None:
        """Pre-saved token makes provider authenticated on init."""
        # Arrange
        key = Fernet.generate_key()
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=key,
        )
        tokens = _make_valid_tokens()
        storage.save(
            "gemini_oauth",
            "user@example.com",
            tokens.model_dump(mode="json"),
        )

        # Act
        provider = GeminiOAuthProvider(
            token_storage=storage,
            account_id="user@example.com",
        )

        # Assert
        assert provider.is_authenticated is True

    async def test_gemini_oauth_provider_send_raises_when_not_authenticated(
        self,
        tmp_path: Path,
    ) -> None:
        """send() without authentication raises AuthenticationError."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = GeminiOAuthProvider(token_storage=storage)
        request = LLMRequest(prompt="Say hello")

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await provider.send(request)

    def test_gemini_oauth_provider_uses_cloudaicompanion_endpoint(
        self,
        tmp_path: Path,
    ) -> None:
        """GeminiOAuthProvider endpoint URL contains cloudaicompanion."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = GeminiOAuthProvider(token_storage=storage)

        # Act & Assert
        assert "cloudaicompanion" in provider.ENDPOINT_URL
