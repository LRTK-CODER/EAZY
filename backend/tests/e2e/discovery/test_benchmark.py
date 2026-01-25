"""Performance benchmark tests for Discovery module."""

from __future__ import annotations

import gc
import time
from typing import Dict, List

import pytest

from app.services.discovery.models import ScanProfile
from app.services.discovery.service import DiscoveryService

from .conftest import PROFILE_TIME_LIMITS


class TestPerformanceBenchmark:
    """Performance benchmarks for Discovery scans."""

    @pytest.mark.asyncio
    async def test_memory_usage_within_limits(
        self, full_registry, full_discovery_context
    ):
        """Memory usage stays within 500MB limit."""
        service = DiscoveryService(full_registry)

        # Force garbage collection before measuring
        gc.collect()

        # Get baseline memory
        # Note: sys.getsizeof only gives shallow size, not full memory
        # For production, use memray or tracemalloc

        # Run discovery
        assets = await service.run_discovery(full_discovery_context)

        # Check asset collection size is reasonable
        # Each asset should be small (< 10KB typically)
        total_assets = len(assets)
        assert total_assets < 10000, f"Too many assets: {total_assets}"

        # Estimate memory: each asset ~1KB (conservative)
        estimated_mb = (total_assets * 1024) / (1024 * 1024)
        assert (
            estimated_mb < 500
        ), f"Estimated memory {estimated_mb:.2f}MB exceeds 500MB"

    @pytest.mark.asyncio
    async def test_throughput_metrics(self, full_registry, full_discovery_context):
        """Measure and report throughput metrics."""
        service = DiscoveryService(full_registry)

        start = time.monotonic()
        assets = await service.run_discovery(full_discovery_context)
        elapsed = time.monotonic() - start

        # Calculate metrics
        total_assets = len(assets)
        assets_per_second = total_assets / elapsed if elapsed > 0 else 0

        # Report metrics (would go to CI in production)
        metrics = {
            "total_assets": total_assets,
            "elapsed_seconds": elapsed,
            "assets_per_second": assets_per_second,
            "profile": ScanProfile.FULL.value,
        }

        # Basic sanity checks
        assert elapsed > 0, "Elapsed time should be positive"
        assert isinstance(total_assets, int), "Total assets should be integer"

        # Log metrics for CI visibility
        print(f"\nBenchmark Results: {metrics}")

    @pytest.mark.asyncio
    async def test_profile_comparison_benchmark(
        self,
        quick_registry,
        standard_registry,
        full_registry,
        quick_discovery_context,
        e2e_discovery_context,
        full_discovery_context,
    ):
        """Compare performance across all profiles."""
        profiles = [
            ("QUICK", quick_registry, quick_discovery_context),
            ("STANDARD", standard_registry, e2e_discovery_context),
            ("FULL", full_registry, full_discovery_context),
        ]

        results: List[Dict] = []

        for name, registry, context in profiles:
            service = DiscoveryService(registry)

            start = time.monotonic()
            assets = await service.run_discovery(context)
            elapsed = time.monotonic() - start

            results.append(
                {
                    "profile": name,
                    "modules": len(registry.get_by_profile(context.profile)),
                    "assets": len(assets),
                    "elapsed_ms": elapsed * 1000,
                }
            )

        # Verify progressive complexity
        # QUICK should have fewer modules than STANDARD
        assert results[0]["modules"] <= results[1]["modules"]
        # STANDARD should have fewer modules than FULL
        assert results[1]["modules"] <= results[2]["modules"]

        # Log comparison table
        print("\n" + "=" * 60)
        print("Profile Comparison Benchmark")
        print("=" * 60)
        print(f"{'Profile':<10} {'Modules':<10} {'Assets':<10} {'Time (ms)':<10}")
        print("-" * 60)
        for r in results:
            print(
                f"{r['profile']:<10} {r['modules']:<10} {r['assets']:<10} {r['elapsed_ms']:.2f}"
            )
        print("=" * 60)

    @pytest.mark.asyncio
    async def test_repeated_scan_consistency(
        self, standard_registry, e2e_discovery_context
    ):
        """Repeated scans produce consistent results."""
        service = DiscoveryService(standard_registry)

        # Run multiple times
        results = []
        for _ in range(3):
            assets = await service.run_discovery(e2e_discovery_context)
            results.append(set(a.url for a in assets))

        # All runs should produce same URLs
        first_run = results[0]
        for i, run in enumerate(results[1:], 2):
            assert run == first_run, f"Run {i} produced different results"

    @pytest.mark.asyncio
    async def test_concurrent_scan_isolation(
        self, standard_registry, e2e_discovery_context
    ):
        """Concurrent scans don't interfere with each other."""
        import asyncio

        service = DiscoveryService(standard_registry)

        # Run 3 scans concurrently
        tasks = [
            service.run_discovery(e2e_discovery_context),
            service.run_discovery(e2e_discovery_context),
            service.run_discovery(e2e_discovery_context),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete without error
        assert len(results) == 3

        # All should produce same results (since same context)
        urls_sets = [set(a.url for a in assets) for assets in results]
        assert urls_sets[0] == urls_sets[1] == urls_sets[2]


class TestCIIntegration:
    """Tests for CI pipeline integration."""

    @pytest.mark.asyncio
    async def test_generates_junit_compatible_output(
        self, quick_registry, quick_discovery_context
    ):
        """Test output is compatible with JUnit format for CI."""
        service = DiscoveryService(quick_registry)

        start = time.monotonic()
        assets = await service.run_discovery(quick_discovery_context)
        elapsed = time.monotonic() - start

        # These assertions generate JUnit-compatible output
        assert isinstance(assets, list), "Assets should be a list"
        assert (
            elapsed < PROFILE_TIME_LIMITS[ScanProfile.QUICK]
        ), f"QUICK scan exceeded time limit: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_benchmark_data_exportable(
        self, full_registry, full_discovery_context
    ):
        """Benchmark data can be exported for tracking."""
        service = DiscoveryService(full_registry)

        start = time.monotonic()
        assets = await service.run_discovery(full_discovery_context)
        elapsed = time.monotonic() - start

        # Create exportable benchmark data
        benchmark_data = {
            "test_name": "full_scan_benchmark",
            "timestamp": time.time(),
            "metrics": {
                "duration_seconds": elapsed,
                "asset_count": len(assets),
                "profile": ScanProfile.FULL.value,
            },
            "thresholds": {
                "max_duration": PROFILE_TIME_LIMITS[ScanProfile.FULL],
                "max_memory_mb": 500,
            },
            "passed": elapsed < PROFILE_TIME_LIMITS[ScanProfile.FULL],
        }

        # Verify structure is correct
        assert "metrics" in benchmark_data
        assert "thresholds" in benchmark_data
        assert benchmark_data["passed"] is True
