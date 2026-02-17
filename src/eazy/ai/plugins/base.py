"""Authentication plugin abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AuthPlugin(ABC):
    """Abstract base class for authentication plugins.

    Subclasses must implement authenticate, refresh,
    and is_expired.
    """

    @abstractmethod
    async def authenticate(self, **kwargs: Any) -> bool:
        """Perform authentication flow.

        Args:
            **kwargs: Plugin-specific authentication parameters.

        Returns:
            True if authentication succeeded.
        """

    @abstractmethod
    async def refresh(self) -> bool:
        """Refresh expired credentials.

        Returns:
            True if refresh succeeded.
        """

    @abstractmethod
    def is_expired(self) -> bool:
        """Check whether current credentials are expired.

        Returns:
            True if credentials are expired.
        """
