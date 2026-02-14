"""Unit tests for AccountManager multi-account management."""

from __future__ import annotations

import pytest

from eazy.ai.account_manager import AccountManager
from eazy.ai.exceptions import RateLimitError
from eazy.ai.models import AccountInfo, AccountStatus, ProviderType
from eazy.ai.providers.gemini_api import GeminiAPIProvider


class TestAccountManager:
    def test_account_manager_register_account(self):
        """register() stores account and provider pair."""
        manager = AccountManager()
        account = AccountInfo(
            account_id="user1@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider = GeminiAPIProvider(api_keys=["key1"])

        manager.register(account, provider)

        result_account, result_provider = manager.get_active(
            ProviderType.GEMINI_API,
        )
        assert result_account.account_id == "user1@test.com"
        assert result_provider is provider

    def test_account_manager_get_active_account(self):
        """get_active() returns first active account."""
        manager = AccountManager()
        account1 = AccountInfo(
            account_id="first@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="second@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)

        result_account, _ = manager.get_active(ProviderType.GEMINI_API)
        assert result_account.account_id == "first@test.com"

    def test_account_manager_switch_on_rate_limit(self):
        """mark_rate_limited() causes get_active() to return next account."""
        manager = AccountManager()
        account1 = AccountInfo(
            account_id="first@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="second@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)

        manager.mark_rate_limited("first@test.com")

        result_account, result_provider = manager.get_active(
            ProviderType.GEMINI_API,
        )
        assert result_account.account_id == "second@test.com"
        assert result_provider is provider2

    def test_account_manager_tracks_account_status(self):
        """mark_rate_limited() sets status to RATE_LIMITED."""
        manager = AccountManager()
        account = AccountInfo(
            account_id="user@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider = GeminiAPIProvider(api_keys=["key1"])

        manager.register(account, provider)
        manager.mark_rate_limited("user@test.com")

        assert account.status == AccountStatus.RATE_LIMITED

    def test_account_manager_round_robin_rotation(self):
        """rotate() cycles through accounts."""
        manager = AccountManager()
        account1 = AccountInfo(
            account_id="first@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="second@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)

        rotated_account, _ = manager.rotate(ProviderType.GEMINI_API)
        assert rotated_account.account_id == "second@test.com"

        rotated_account, _ = manager.rotate(ProviderType.GEMINI_API)
        assert rotated_account.account_id == "first@test.com"

    def test_account_manager_skips_rate_limited_accounts(self):
        """rotate() skips rate-limited accounts."""
        manager = AccountManager()
        account1 = AccountInfo(
            account_id="first@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="second@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account3 = AccountInfo(
            account_id="third@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])
        provider3 = GeminiAPIProvider(api_keys=["key3"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)
        manager.register(account3, provider3)

        manager.mark_rate_limited("second@test.com")

        rotated_account, _ = manager.rotate(ProviderType.GEMINI_API)
        assert rotated_account.account_id == "third@test.com"

    def test_account_manager_raises_when_all_exhausted(self):
        """All accounts rate-limited raises RateLimitError."""
        manager = AccountManager()
        account1 = AccountInfo(
            account_id="first@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="second@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)

        manager.mark_rate_limited("first@test.com")
        manager.mark_rate_limited("second@test.com")

        with pytest.raises(RateLimitError):
            manager.get_active(ProviderType.GEMINI_API)
