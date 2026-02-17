"""Token storage for LLM provider credentials."""

from __future__ import annotations

import json
from pathlib import Path

from eazy.ai.models import AuthEntry


class TokenStorage:
    """JSON file-based credential storage.

    Stores and retrieves AuthEntry instances keyed by
    provider name. File is created on first write.

    Attributes:
        _path: Path to the auth.json file.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".eazy" / "auth.json"

    def load(self) -> dict[str, AuthEntry]:
        """Load all entries from the storage file.

        Returns:
            Dictionary mapping provider names to AuthEntry
            instances. Returns empty dict if file doesn't exist.
        """
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text())
        return {k: AuthEntry.model_validate(v) for k, v in raw.items()}

    def save(self, key: str, entry: AuthEntry) -> None:
        """Save an entry to storage.

        Creates parent directories if they don't exist.

        Args:
            key: Provider name key.
            entry: Authentication entry to store.
        """
        data = self.load()
        data[key] = entry
        self._write(data)

    def get(self, key: str) -> AuthEntry | None:
        """Retrieve a single entry by key.

        Args:
            key: Provider name to look up.

        Returns:
            The AuthEntry, or None if not found.
        """
        return self.load().get(key)

    def remove(self, key: str) -> None:
        """Remove an entry from storage.

        Args:
            key: Provider name to remove.
        """
        data = self.load()
        data.pop(key, None)
        self._write(data)

    def _write(self, data: dict[str, AuthEntry]) -> None:
        """Write data dict to the JSON file.

        Args:
            data: Dictionary of entries to persist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = {k: v.model_dump(mode="json") for k, v in data.items()}
        self._path.write_text(json.dumps(serialized, indent=2))
