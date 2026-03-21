"""Plugin registry — manages scanner plugin entries via registry.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
SCANNER_CATEGORY = Literal[
    "js_analysis",
    "osint",
    "directory",
    "waf_fingerprint",
    "tech_stack",
    "error_pattern",
]

# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------


class PluginEntry(BaseModel):
    """Metadata for a single scanner plugin."""

    name: str = Field(..., description="Unique plugin name")
    category: SCANNER_CATEGORY = Field(..., description="Scanner category")
    module_path: str = Field(..., description="Dotted module path to plugin class")
    enabled: bool = Field(default=True, description="Whether the plugin is active")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Plugin-specific config"
    )


# ---------------------------------------------------------------------------
# PluginRegistry
# ---------------------------------------------------------------------------


class PluginRegistry:
    """Loads and manages scanner plugin entries from a YAML registry file."""

    def __init__(
        self, registry_path: str = "src/agents/scanners/registry.yaml"
    ) -> None:
        self._registry_path = Path(registry_path)
        self._plugins: dict[str, PluginEntry] = {}

    def load(self) -> None:
        """Load plugin entries from the YAML registry file.

        If the file does not exist, the registry remains empty.
        """
        self._plugins.clear()
        if not self._registry_path.is_file():
            return

        raw = self._registry_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return

        plugins_list = data.get("plugins", [])
        if not isinstance(plugins_list, list):
            return

        for item in plugins_list:
            entry = PluginEntry(**item)
            self._plugins[entry.name] = entry

    def get_active_plugins(self) -> list[PluginEntry]:
        """Return all enabled plugin entries."""
        return [e for e in self._plugins.values() if e.enabled]

    def get_plugins_by_category(self, category: str) -> list[PluginEntry]:
        """Return enabled plugins matching the given category."""
        return [
            e for e in self._plugins.values() if e.category == category and e.enabled
        ]

    def register(self, entry: PluginEntry) -> None:
        """Register a plugin entry at runtime.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        if entry.name in self._plugins:
            msg = f"Plugin already registered: {entry.name}"
            raise ValueError(msg)
        self._plugins[entry.name] = entry

    def is_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is registered and enabled.

        Returns False if the plugin is not found.
        """
        entry = self._plugins.get(plugin_name)
        if entry is None:
            return False
        return entry.enabled
