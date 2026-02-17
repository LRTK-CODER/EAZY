from __future__ import annotations

import pytest
from pydantic import ValidationError

from eazy.ai.models import ApiKeyEntry, AuthEntry, LLMResponse, OAuthTokens


class TestLLMResponse:
    def test_creation_with_all_fields_stores_values(self) -> None:
        """All fields are stored correctly when explicitly provided."""
        response = LLMResponse(
            content="Hello",
            model="gemini-1.5-pro",
            input_tokens=10,
            output_tokens=20,
            finish_reason="stop",
        )

        assert response.content == "Hello"
        assert response.model == "gemini-1.5-pro"
        assert response.input_tokens == 10
        assert response.output_tokens == 20
        assert response.finish_reason == "stop"

    def test_defaults_are_applied_when_optional_fields_omitted(self) -> None:
        """Optional fields default to zero/None when not provided."""
        response = LLMResponse(content="Hi", model="gemini-1.5-flash")

        assert response.input_tokens == 0
        assert response.output_tokens == 0
        assert response.finish_reason is None

    def test_frozen_raises_validation_error_on_attribute_assignment(
        self,
    ) -> None:
        """Assigning to a frozen model field raises ValidationError."""
        response = LLMResponse(content="Hi", model="gemini-1.5-flash")

        with pytest.raises(ValidationError):
            response.content = "changed"  # type: ignore[misc]


class TestOAuthTokens:
    def test_creation_stores_all_fields(self) -> None:
        """All OAuth token fields are stored correctly."""
        tokens = OAuthTokens(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=1_700_000_000_000,
        )

        assert tokens.access_token == "access123"
        assert tokens.refresh_token == "refresh456"
        assert tokens.expires_at == 1_700_000_000_000

    def test_frozen_raises_validation_error_on_attribute_assignment(
        self,
    ) -> None:
        """Assigning to a frozen model field raises ValidationError."""
        tokens = OAuthTokens(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=1_700_000_000_000,
        )

        with pytest.raises(ValidationError):
            tokens.access_token = "changed"  # type: ignore[misc]


class TestApiKeyEntry:
    def test_creation_stores_key(self) -> None:
        """Key field is stored correctly on creation."""
        entry = ApiKeyEntry(key="my-secret-api-key")

        assert entry.key == "my-secret-api-key"

    def test_masked_key_long_shows_first_and_last_four_chars(self) -> None:
        """Keys longer than 8 chars are masked as 'abcd...efgh'."""
        entry = ApiKeyEntry(key="abcd1234efgh")

        assert entry.masked_key == "abcd...efgh"

    def test_masked_key_short_returns_four_asterisks(self) -> None:
        """Keys 8 chars or shorter are masked as '****'."""
        entry = ApiKeyEntry(key="short")

        assert entry.masked_key == "****"


class TestAuthEntry:
    def test_oauth_type_stores_oauth_tokens_and_null_api(self) -> None:
        """AuthEntry with type='oauth' holds OAuthTokens and api=None."""
        tokens = OAuthTokens(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=1_700_000_000_000,
        )
        entry = AuthEntry(type="oauth", oauth=tokens, api=None)

        assert entry.type == "oauth"
        assert entry.oauth == tokens
        assert entry.api is None

    def test_api_type_stores_api_key_entry_and_null_oauth(self) -> None:
        """AuthEntry with type='api' holds ApiKeyEntry and oauth=None."""
        api_key = ApiKeyEntry(key="abcd1234efgh")
        entry = AuthEntry(type="api", api=api_key, oauth=None)

        assert entry.type == "api"
        assert entry.api == api_key
        assert entry.oauth is None
