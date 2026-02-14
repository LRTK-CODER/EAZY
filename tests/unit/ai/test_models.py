"""Unit tests for LLM data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eazy.ai.models import (
    AccountInfo,
    AccountStatus,
    BillingType,
    LLMRequest,
    LLMResponse,
    ProviderConfig,
    ProviderType,
    RateLimitInfo,
)


class TestBillingType:
    def test_billing_type_enum_has_subscription_per_token_free(self):
        """BillingType should have subscription, per_token, free values."""
        expected = {"subscription", "per_token", "free"}
        actual = {member.value for member in BillingType}
        assert actual == expected


class TestProviderType:
    def test_provider_type_enum_has_gemini_oauth_antigravity_gemini_api(
        self,
    ):
        """ProviderType should have gemini_oauth, antigravity, gemini_api."""
        expected = {"gemini_oauth", "antigravity", "gemini_api"}
        actual = {member.value for member in ProviderType}
        assert actual == expected


class TestAccountStatus:
    def test_account_status_enum_has_active_rate_limited_expired_revoked(
        self,
    ):
        """AccountStatus should have active, rate_limited, expired, revoked."""
        expected = {"active", "rate_limited", "expired", "revoked"}
        actual = {member.value for member in AccountStatus}
        assert actual == expected


class TestLLMRequest:
    def test_llm_request_creation_with_prompt_and_model(self):
        """LLMRequest should store prompt and model."""
        request = LLMRequest(prompt="Hello", model="gemini-2.0-flash")
        assert request.prompt == "Hello"
        assert request.model == "gemini-2.0-flash"

    def test_llm_request_default_model_is_gemini_flash(self):
        """LLMRequest model should default to gemini-2.0-flash."""
        request = LLMRequest(prompt="Hello")
        assert request.model == "gemini-2.0-flash"

    def test_llm_request_default_temperature_is_0_7(self):
        """LLMRequest temperature should default to 0.7."""
        request = LLMRequest(prompt="Hello")
        assert request.temperature == 0.7

    def test_llm_request_frozen_immutable(self):
        """LLMRequest should be immutable (frozen=True)."""
        request = LLMRequest(prompt="Hello")
        with pytest.raises(ValidationError):
            request.prompt = "Changed"


class TestLLMResponse:
    def test_llm_response_creation_with_content_and_model(self):
        """LLMResponse should store content, model, and provider_type."""
        response = LLMResponse(
            content="Hi there",
            model="gemini-2.0-flash",
            provider_type=ProviderType.GEMINI_API,
        )
        assert response.content == "Hi there"
        assert response.model == "gemini-2.0-flash"
        assert response.provider_type == ProviderType.GEMINI_API

    def test_llm_response_includes_token_usage(self):
        """LLMResponse should track input and output token counts."""
        response = LLMResponse(
            content="Hi",
            model="gemini-2.0-flash",
            provider_type=ProviderType.GEMINI_API,
            input_tokens=10,
            output_tokens=5,
        )
        assert response.input_tokens == 10
        assert response.output_tokens == 5

    def test_llm_response_frozen_immutable(self):
        """LLMResponse should be immutable (frozen=True)."""
        response = LLMResponse(
            content="Hi",
            model="gemini-2.0-flash",
            provider_type=ProviderType.GEMINI_API,
        )
        with pytest.raises(ValidationError):
            response.content = "Changed"


class TestRateLimitInfo:
    def test_rate_limit_info_tracks_remaining_requests(self):
        """RateLimitInfo should track remaining minute and day requests."""
        info = RateLimitInfo(
            max_requests_per_minute=15,
            max_requests_per_day=1500,
            remaining_minute=10,
            remaining_day=1000,
        )
        assert info.max_requests_per_minute == 15
        assert info.max_requests_per_day == 1500
        assert info.remaining_minute == 10
        assert info.remaining_day == 1000

    def test_rate_limit_info_is_exceeded_when_remaining_zero(self):
        """RateLimitInfo is_exceeded should be True when remaining zero."""
        info = RateLimitInfo(
            max_requests_per_minute=15,
            max_requests_per_day=1500,
            remaining_minute=0,
            remaining_day=1000,
        )
        assert info.is_exceeded is True

        info2 = RateLimitInfo(
            max_requests_per_minute=15,
            max_requests_per_day=1500,
            remaining_minute=10,
            remaining_day=0,
        )
        assert info2.is_exceeded is True

        info3 = RateLimitInfo(
            max_requests_per_minute=15,
            max_requests_per_day=1500,
            remaining_minute=10,
            remaining_day=1000,
        )
        assert info3.is_exceeded is False


class TestAccountInfo:
    def test_account_info_creation_with_defaults(self):
        """AccountInfo should default status to ACTIVE."""
        account = AccountInfo(
            account_id="user@example.com",
            provider_type=ProviderType.GEMINI_API,
        )
        assert account.account_id == "user@example.com"
        assert account.provider_type == ProviderType.GEMINI_API
        assert account.status == AccountStatus.ACTIVE
        assert account.rate_limit is None
        assert account.last_used is None


class TestProviderConfig:
    def test_provider_config_creation(self):
        """ProviderConfig should store provider_type and credentials."""
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_API,
            api_key="test-key-123",
        )
        assert config.provider_type == ProviderType.GEMINI_API
        assert config.api_key == "test-key-123"
        assert config.oauth_client_id is None
        assert config.oauth_client_secret is None
        assert config.endpoint_url is None
