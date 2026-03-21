"""Scanner plugin infrastructure — ABC, registry, executor, and plugin entries."""

from src.agents.scanners.base import ScannerPlugin
from src.agents.scanners.executor import PluginStatus, ScannerExecutor, ScanResult
from src.agents.scanners.registry import PluginEntry, PluginRegistry

__all__ = [
    "PluginEntry",
    "PluginRegistry",
    "PluginStatus",
    "ScannerExecutor",
    "ScannerPlugin",
    "ScanResult",
]
