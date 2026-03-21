"""ScannerExecutor — runs scanner plugins concurrently via asyncio.gather."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from pydantic import BaseModel, Field

from src.agents.scanners.base import ScannerPlugin


class PluginStatus(BaseModel):
    """Execution status for a single scanner plugin."""

    plugin_name: str = Field(..., description="Plugin name")
    category: str = Field(..., description="Plugin category")
    success: bool = Field(..., description="Whether the scan succeeded")
    error: str | None = Field(default=None, description="Error message if failed")


class ScanResult(BaseModel):
    """Aggregated result of parallel scanner execution."""

    results_by_category: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Scan results grouped by category",
    )
    plugin_statuses: list[PluginStatus] = Field(
        default_factory=list,
        description="Per-plugin execution status",
    )
    elapsed_time: float = Field(..., description="Total execution time in seconds")


class ScannerExecutor:
    """Executes scanner plugins concurrently."""

    def __init__(self, plugins: list[ScannerPlugin]) -> None:
        self._plugins = plugins

    async def execute(
        self,
        target: str,
        config: dict[str, Any] | None = None,
    ) -> ScanResult:
        """Run all plugins in parallel via asyncio.gather."""
        start = time.monotonic()

        tasks = [self._run_plugin(p, target, config or {}) for p in self._plugins]
        outcomes = await asyncio.gather(*tasks)

        results_by_category: dict[str, list[dict[str, Any]]] = {}
        statuses: list[PluginStatus] = []

        for name, category, result, error in outcomes:
            success = error is None
            statuses.append(
                PluginStatus(
                    plugin_name=name,
                    category=category,
                    success=success,
                    error=error,
                )
            )
            if success and result is not None:
                results_by_category.setdefault(category, []).append(result)

        elapsed = time.monotonic() - start
        return ScanResult(
            results_by_category=results_by_category,
            plugin_statuses=statuses,
            elapsed_time=elapsed,
        )

    async def _run_plugin(
        self,
        plugin: ScannerPlugin,
        target: str,
        config: dict[str, Any],
    ) -> tuple[str, str, dict[str, Any] | None, str | None]:
        """Execute a single plugin with error isolation."""
        try:
            result = await plugin.scan(target, config)
        except Exception as exc:  # noqa: BLE001
            return (plugin.name, plugin.category, None, str(exc))
        return (plugin.name, plugin.category, result, None)
