"""Unit tests for AntigravityOAuthProvider.

Test Coverage:
- ABC compliance (LLMProvider)
- Capability properties (oauth, multi-account, billing)
- OAuth authentication flow
- Send request with Bearer token auth
- Endpoint URL verification
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import respx
from cryptography.fernet import Fernet

from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    OAuthTokens,
    ProviderType,
)
from eazy.ai.provider import LLMProvider
from eazy.ai.providers.antigravity import AntigravityOAuthProvider
from eazy.ai.token_storage import TokenStorage

ANTIGRAVITY_BASE = "https://autopush-cloudaicompanion.sandbox.googleapis.com/v1beta"

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


def _make_valid_tokens() -> OAuthTokens:
    """Create valid OAuthTokens for testing."""
    return OAuthTokens(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)),
        scope=("https://www.googleapis.com/auth/generative-language"),
    )


class TestAntigravityOAuthProvider:
    """Test suite for AntigravityOAuthProvider."""

    def test_antigravity_provider_implements_llm_provider(
        self,
        tmp_path: Path,
    ) -> None:
        """AntigravityOAuthProvider is a subclass of LLMProvider."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )

        # Act
        provider = AntigravityOAuthProvider(
            token_storage=storage,
        )

        # Assert
        assert isinstance(provider, LLMProvider)

    def test_antigravity_provider_capability_oauth_supported(
        self,
        tmp_path: Path,
    ) -> None:
        """AntigravityOAuthProvider supports OAuth."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = AntigravityOAuthProvider(
            token_storage=storage,
        )

        # Act & Assert
        assert provider.supports_oauth is True

    def test_antigravity_provider_capability_multi_account(
        self,
        tmp_path: Path,
    ) -> None:
        """AntigravityOAuthProvider supports multi-account."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = AntigravityOAuthProvider(
            token_storage=storage,
        )

        # Act & Assert
        assert provider.supports_multi_account is True

    def test_antigravity_provider_billing_type_subscription(
        self,
        tmp_path: Path,
    ) -> None:
        """AntigravityOAuthProvider uses subscription billing."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = AntigravityOAuthProvider(
            token_storage=storage,
        )

        # Act & Assert
        assert provider.billing_type == BillingType.SUBSCRIPTION

    async def test_antigravity_provider_authenticate_triggers_oauth_flow(
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

        provider = AntigravityOAuthProvider(
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
    async def test_antigravity_provider_send_with_valid_token(
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

        provider = AntigravityOAuthProvider(
            token_storage=storage,
            oauth_engine=mock_engine,
        )
        await provider.authenticate(
            code="code",
            redirect_uri="http://localhost",
            account_id="user@example.com",
        )

        route = respx.post(
            url__startswith=f"{ANTIGRAVITY_BASE}/models/",
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
        assert response.provider_type == ProviderType.ANTIGRAVITY
        assert response.input_tokens == 5

        # Verify Bearer auth header
        sent_request = route.calls[0].request
        assert sent_request.headers["authorization"] == ("Bearer test-access-token")

    def test_antigravity_provider_uses_antigravity_endpoint(
        self,
        tmp_path: Path,
    ) -> None:
        """AntigravityOAuthProvider endpoint has antigravity host."""
        # Arrange
        storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        provider = AntigravityOAuthProvider(
            token_storage=storage,
        )

        # Act & Assert
        assert "autopush-cloudaicompanion" in provider.ENDPOINT_URL
        assert "sandbox" in provider.ENDPOINT_URL
