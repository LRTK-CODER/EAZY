"""Scanner plugin infrastructure — ABC, registry, and plugin entries."""

from src.agents.scanners.base import ScannerPlugin
from src.agents.scanners.registry import PluginEntry, PluginRegistry

__all__ = ["PluginEntry", "PluginRegistry", "ScannerPlugin"]
