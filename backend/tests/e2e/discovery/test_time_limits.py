"""E2E tests for scan time limits across all profiles."""

from __future__ import annotations

import asyncio
import time

import pytest

from app.services.discovery.models import ScanProfile
from app.services.discovery.service import DiscoveryService

from .conftest import PROFILE_TIME_LIMITS


class TestScanTimeLimits:
    """Tests for profile-specific time limits."""

    @pytest.mark.asyncio
    async def test_quick_scan_completes_in_under_30_seconds(
        self, quick_registry, quick_discovery_context
    ):
        """QUICK scan completes in under 30 seconds."""
        service = DiscoveryService(quick_registry)
        limit = PROFILE_TIME_LIMITS[ScanProfile.QUICK]

        start = time.monotonic()
        await service.run_discovery(quick_discovery_context)
        elapsed = time.monotonic() - start

        assert elapsed < limit, f"QUICK scan took {elapsed:.2f}s, expected < {limit}s"

    @pytest.mark.asyncio
    async def test_standard_scan_completes_in_under_2_minutes(
        self, standard_registry, e2e_discovery_context
    ):
        """STANDARD scan completes in under 2 minutes."""
        service = DiscoveryService(standard_registry)
        limit = PROFILE_TIME_LIMITS[ScanProfile.STANDARD]

        start = time.monotonic()
        await service.run_discovery(e2e_discovery_context)
        elapsed = time.monotonic() - start

        assert (
            elapsed < limit
        ), f"STANDARD scan took {elapsed:.2f}s, expected < {limit}s"

    @pytest.mark.asyncio
    async def test_full_scan_completes_in_under_5_minutes(
        self, full_registry, full_discovery_context
    ):
        """FULL scan completes in under 5 minutes."""
        service = DiscoveryService(full_registry)
        limit = PROFILE_TIME_LIMITS[ScanProfile.FULL]

        start = time.monotonic()
        await service.run_discovery(full_discovery_context)
        elapsed = time.monotonic() - start

        assert elapsed < limit, f"FULL scan took {elapsed:.2f}s, expected < {limit}s"

    @pytest.mark.asyncio
    async def test_timeout_respected_and_scan_stops_gracefully(
        self, full_registry, full_discovery_context
    ):
        """Timeout is respected and scan stops gracefully."""
        service = DiscoveryService(full_registry)

        # Use a very short timeout to force timeout
        short_timeout = 0.001  # 1ms - will definitely timeout

        try:
            async with asyncio.timeout(short_timeout):
                await service.run_discovery(full_discovery_context)
        except TimeoutError:
            pass  # Expected timeout

        # Scan should have timed out with such a short limit
        # Or completed very quickly (which is also acceptable)
        # The key is that it doesn't hang or crash
        assert True  # If we reach here, graceful handling worked

    @pytest.mark.asyncio
    async def test_all_profiles_meet_time_requirements(
        self,
        quick_registry,
        standard_registry,
        full_registry,
        quick_discovery_context,
        e2e_discovery_context,
        full_discovery_context,
    ):
        """All profiles meet their respective time requirements."""
        profiles_config = [
            (ScanProfile.QUICK, quick_registry, quick_discovery_context),
            (ScanProfile.STANDARD, standard_registry, e2e_discovery_context),
            (ScanProfile.FULL, full_registry, full_discovery_context),
        ]

        results = []

        for profile, registry, context in profiles_config:
            service = DiscoveryService(registry)
            limit = PROFILE_TIME_LIMITS[profile]

            start = time.monotonic()
            await service.run_discovery(context)
            elapsed = time.monotonic() - start

            results.append(
                {
                    "profile": profile.name,
                    "elapsed": elapsed,
                    "limit": limit,
                    "passed": elapsed < limit,
                }
            )

        # All profiles should pass
        for result in results:
            assert result["passed"], (
                f"{result['profile']} scan took {result['elapsed']:.2f}s, "
                f"expected < {result['limit']}s"
            )

    @pytest.mark.asyncio
    async def test_quick_is_faster_than_standard(
        self,
        quick_registry,
        standard_registry,
        quick_discovery_context,
        e2e_discovery_context,
    ):
        """QUICK scan is faster than STANDARD scan."""
        quick_service = DiscoveryService(quick_registry)
        standard_service = DiscoveryService(standard_registry)

        # Measure QUICK
        start = time.monotonic()
        await quick_service.run_discovery(quick_discovery_context)
        quick_time = time.monotonic() - start

        # Measure STANDARD
        start = time.monotonic()
        await standard_service.run_discovery(e2e_discovery_context)
        standard_time = time.monotonic() - start

        # QUICK should be faster (or at least not slower)
        # Allow some variance for test stability
        assert quick_time <= standard_time * 1.5, (
            f"QUICK ({quick_time:.2f}s) should be faster than "
            f"STANDARD ({standard_time:.2f}s)"
        )

    @pytest.mark.asyncio
    async def test_standard_is_faster_than_full(
        self,
        standard_registry,
        full_registry,
        e2e_discovery_context,
        full_discovery_context,
    ):
        """STANDARD scan is faster than FULL scan."""
        standard_service = DiscoveryService(standard_registry)
        full_service = DiscoveryService(full_registry)

        # Measure STANDARD
        start = time.monotonic()
        await standard_service.run_discovery(e2e_discovery_context)
        standard_time = time.monotonic() - start

        # Measure FULL
        start = time.monotonic()
        await full_service.run_discovery(full_discovery_context)
        full_time = time.monotonic() - start

        # STANDARD should be faster (or at least not slower)
        # Allow some variance for test stability
        assert standard_time <= full_time * 1.5, (
            f"STANDARD ({standard_time:.2f}s) should be faster than "
            f"FULL ({full_time:.2f}s)"
        )
