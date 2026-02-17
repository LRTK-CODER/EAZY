from __future__ import annotations

import pytest

from eazy.ai.plugins.base import AuthPlugin


class TestAuthPlugin:
    """Test suite for AuthPlugin abstract base class."""

    def test_cannot_instantiate_abc(self) -> None:
        """AuthPlugin ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AuthPlugin()  # type: ignore

    def test_concrete_requires_authenticate(self) -> None:
        """Concrete class missing authenticate raises TypeError."""

        class Incomplete(AuthPlugin):
            async def refresh(self) -> bool:
                return True

            def is_expired(self) -> bool:
                return False

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore

    def test_concrete_requires_refresh(self) -> None:
        """Concrete class missing refresh raises TypeError."""

        class Incomplete(AuthPlugin):
            async def authenticate(self, **kwargs: dict) -> bool:
                return True

            def is_expired(self) -> bool:
                return False

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore

    def test_concrete_requires_is_expired(self) -> None:
        """Concrete class missing is_expired raises TypeError."""

        class Incomplete(AuthPlugin):
            async def authenticate(self, **kwargs: dict) -> bool:
                return True

            async def refresh(self) -> bool:
                return True

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore
