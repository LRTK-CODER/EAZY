"""Tests for scanner plugin registry — ABC, PluginEntry, and PluginRegistry."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.agents.scanners.base import ScannerPlugin
from src.agents.scanners.registry import PluginEntry, PluginRegistry

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "scanners"
REGISTRY_YAML = str(FIXTURES_DIR / "registry.yaml")


class _ConcreteScanner(ScannerPlugin):
    """Minimal concrete implementation for testing."""

    @property
    def category(self) -> str:
        return "js_analysis"

    @property
    def name(self) -> str:
        return "test_scanner"

    async def scan(self, target: str, config: dict[str, Any]) -> dict[str, Any]:
        return {"target": target}

    def parse_output(self, raw: str) -> dict[str, Any]:
        return {"parsed": raw}


class TestScannerPluginABC:
    def test_scanner_plugin_abc_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            ScannerPlugin()  # type: ignore[abstract]

    def test_scanner_plugin_concrete(self) -> None:
        scanner = _ConcreteScanner()
        assert scanner.name == "test_scanner"
        assert scanner.category == "js_analysis"
        assert scanner.parse_output("raw") == {"parsed": "raw"}


class TestPluginEntry:
    def test_plugin_entry_valid(self) -> None:
        entry = PluginEntry(
            name="test",
            category="osint",
            module_path="src.agents.scanners.plugins.test",
        )
        assert entry.name == "test"
        assert entry.category == "osint"
        assert entry.enabled is True
        assert entry.config == {}

    def test_plugin_entry_invalid_category(self) -> None:
        with pytest.raises(ValidationError):
            PluginEntry(
                name="bad",
                category="nonexistent_category",  # type: ignore[arg-type]
                module_path="src.agents.scanners.plugins.bad",
            )


class TestPluginRegistry:
    def test_registry_load_valid_yaml(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        active = registry.get_active_plugins()
        assert len(active) == 5  # 6 total, 1 disabled

    def test_registry_load_missing_file(self) -> None:
        registry = PluginRegistry(registry_path="/nonexistent/registry.yaml")
        registry.load()
        assert registry.get_active_plugins() == []

    def test_registry_get_active_plugins(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        active = registry.get_active_plugins()
        names = {e.name for e in active}
        assert "waf_detector" not in names
        assert "js_beautifier" in names

    def test_registry_disabled_excluded(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        active = registry.get_active_plugins()
        assert all(e.enabled for e in active)
        assert not any(e.name == "waf_detector" for e in active)

    def test_registry_get_by_category(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        osint = registry.get_plugins_by_category("osint")
        assert len(osint) == 1
        assert osint[0].name == "whois_lookup"

    def test_registry_register_runtime(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        new_entry = PluginEntry(
            name="custom_scanner",
            category="tech_stack",
            module_path="src.agents.scanners.plugins.custom",
        )
        registry.register(new_entry)
        assert registry.is_enabled("custom_scanner")

    def test_registry_is_enabled(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        assert registry.is_enabled("js_beautifier") is True
        assert registry.is_enabled("waf_detector") is False
        assert registry.is_enabled("nonexistent") is False

    def test_registry_duplicate_name(self) -> None:
        registry = PluginRegistry(registry_path=REGISTRY_YAML)
        registry.load()
        duplicate = PluginEntry(
            name="js_beautifier",
            category="js_analysis",
            module_path="src.agents.scanners.plugins.dup",
        )
        with pytest.raises(ValueError, match="already registered"):
            registry.register(duplicate)
