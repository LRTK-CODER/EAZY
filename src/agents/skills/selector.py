"""Abstract base class for skill selection (Stage 2/3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.agents.skills.loader import SkillFile


class SkillSelector(ABC):
    """Interface for selecting relevant skills given a vulnerability context."""

    @abstractmethod
    def select(
        self,
        vulnerability_type: str,
        context: dict[str, Any],
    ) -> list[SkillFile]:
        """Return skills relevant to the given vulnerability type and context."""
        ...
