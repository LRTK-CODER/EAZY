"""Abstract base class for scanner plugins (Stage 1 parallel scanners)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ScannerPlugin(ABC):
    """Interface that all scanner plugins must implement."""

    @property
    @abstractmethod
    def category(self) -> str:
        """Scanner category (e.g. 'js_analysis', 'osint')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique scanner name."""
        ...

    @abstractmethod
    async def scan(self, target: str, config: dict[str, Any]) -> dict[str, Any]:
        """Execute the scan against a target URL.

        Args:
            target: The target URL to scan.
            config: Plugin-specific configuration.

        Returns:
            Raw scan results.
        """
        ...

    @abstractmethod
    def parse_output(self, raw: str) -> dict[str, Any]:
        """Parse raw tool output into structured results.

        Args:
            raw: Raw string output from the scanning tool.

        Returns:
            Parsed and structured results.
        """
        ...
