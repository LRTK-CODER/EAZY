"""Multi-account manager with round-robin rotation for LLM providers."""

from __future__ import annotations

from eazy.ai.exceptions import RateLimitError
from eazy.ai.models import AccountInfo, AccountStatus, ProviderType
from eazy.ai.provider import LLMProvider


class AccountManager:
    """Multi-account manager with round-robin rotation.

    Manages multiple LLM provider accounts per provider type, tracks
    their rate-limit status, and provides automatic failover when an
    account is exhausted.
    """

    def __init__(self) -> None:
        self._account_list: dict[
            ProviderType,
            list[tuple[AccountInfo, LLMProvider]],
        ] = {}
        self._current_index: dict[ProviderType, int] = {}

    def register(
        self,
        account: AccountInfo,
        provider: LLMProvider,
    ) -> None:
        """Register an account with its provider.

        Args:
            account: Account metadata including ID and provider type.
            provider: The LLM provider instance for this account.
        """
        pt = account.provider_type
        if pt not in self._account_list:
            self._account_list[pt] = []
            self._current_index[pt] = 0
        self._account_list[pt].append((account, provider))

    def get_active(
        self,
        provider_type: ProviderType,
    ) -> tuple[AccountInfo, LLMProvider]:
        """Get first non-rate-limited account starting from current index.

        Args:
            provider_type: The provider type to look up.

        Returns:
            Tuple of (AccountInfo, LLMProvider) for the active account.

        Raises:
            RateLimitError: If all accounts are rate-limited.
        """
        entries = self._account_list.get(provider_type, [])
        if not entries:
            raise RateLimitError("No accounts registered for this provider type.")

        n = len(entries)
        start = self._current_index.get(provider_type, 0)

        for i in range(n):
            idx = (start + i) % n
            account, provider = entries[idx]
            if account.status != AccountStatus.RATE_LIMITED:
                self._current_index[provider_type] = idx
                return account, provider

        raise RateLimitError("All accounts have exceeded their rate limits.")

    def mark_rate_limited(self, account_id: str) -> None:
        """Mark an account as rate-limited.

        Args:
            account_id: The account identifier to mark.
        """
        for entries in self._account_list.values():
            for account, _ in entries:
                if account.account_id == account_id:
                    account.status = AccountStatus.RATE_LIMITED
                    return

    def rotate(
        self,
        provider_type: ProviderType,
    ) -> tuple[AccountInfo, LLMProvider]:
        """Advance to next account and return it.

        Args:
            provider_type: The provider type to rotate.

        Returns:
            Tuple of (AccountInfo, LLMProvider) for the next account.

        Raises:
            RateLimitError: If all accounts are rate-limited.
        """
        entries = self._account_list.get(provider_type, [])
        if not entries:
            raise RateLimitError("No accounts registered for this provider type.")

        current = self._current_index.get(provider_type, 0)
        self._current_index[provider_type] = (current + 1) % len(entries)

        return self.get_active(provider_type)
