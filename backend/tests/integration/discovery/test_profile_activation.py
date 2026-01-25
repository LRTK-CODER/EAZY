"""Test 6.1.2: Profile-based module activation tests.

TDD RED Phase - DiscoveryService is not yet implemented.
Tests verify that modules are activated correctly based on scan profile.
"""

from __future__ import annotations

import pytest

from app.services.discovery.models import DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# DiscoveryService is not yet implemented - TDD RED Phase
from app.services.discovery.service import DiscoveryService

from .conftest import create_mock_module, create_test_asset


class TestProfileBasedModuleActivation:
    """Test suite for profile-based module activation."""

    def _create_modules_for_all_profiles(
        self, registry: DiscoveryModuleRegistry
    ) -> None:
        """Register modules with different profile support.

        Module distribution:
        - QUICK: 2 modules (quick_only_1, quick_only_2)
        - STANDARD: 6 modules (quick modules + standard_core_1..4)
        - FULL: 10 modules (all modules including full_only_1..4)
        """
        # QUICK only modules (2)
        registry.register(
            create_mock_module(
                name="quick_only_1",
                profiles={ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL},
                assets=[
                    create_test_asset(
                        "https://example.com/quick1", "endpoint", "quick_only_1"
                    )
                ],
            )
        )
        registry.register(
            create_mock_module(
                name="quick_only_2",
                profiles={ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL},
                assets=[
                    create_test_asset(
                        "https://example.com/quick2", "endpoint", "quick_only_2"
                    )
                ],
            )
        )

        # STANDARD core modules (4 additional, total 6 for STANDARD)
        for i in range(1, 5):
            registry.register(
                create_mock_module(
                    name=f"standard_core_{i}",
                    profiles={ScanProfile.STANDARD, ScanProfile.FULL},
                    assets=[
                        create_test_asset(
                            f"https://example.com/standard{i}",
                            "endpoint",
                            f"standard_core_{i}",
                        )
                    ],
                )
            )

        # FULL only modules (4 additional, total 10 for FULL)
        for i in range(1, 5):
            registry.register(
                create_mock_module(
                    name=f"full_only_{i}",
                    profiles={ScanProfile.FULL},
                    assets=[
                        create_test_asset(
                            f"https://example.com/full{i}", "endpoint", f"full_only_{i}"
                        )
                    ],
                )
            )

    @pytest.mark.asyncio
    async def test_quick_profile_activates_minimal_modules(
        self,
        quick_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """QUICK profile should activate only minimal modules (1-2).

        Given: Registry with 10 modules configured for different profiles
        When: DiscoveryService runs with QUICK profile
        Then: Only QUICK-compatible modules (2) are activated
        """
        # Arrange
        self._create_modules_for_all_profiles(empty_registry)
        service = DiscoveryService(registry=empty_registry)

        # Act
        assets = await service.run_discovery(quick_context)

        # Assert
        # QUICK should only activate 2 modules
        sources = {asset.source for asset in assets}
        assert (
            len(sources) <= 2
        ), f"QUICK profile should activate at most 2 modules, got {len(sources)}"
        assert "quick_only_1" in sources or "quick_only_2" in sources
        # Should NOT include standard or full only modules
        for source in sources:
            assert not source.startswith(
                "standard_core_"
            ), f"QUICK should not activate {source}"
            assert not source.startswith(
                "full_only_"
            ), f"QUICK should not activate {source}"

    @pytest.mark.asyncio
    async def test_standard_profile_activates_core_modules(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """STANDARD profile should activate core modules (5-7).

        Given: Registry with 10 modules configured for different profiles
        When: DiscoveryService runs with STANDARD profile
        Then: QUICK + STANDARD modules (6 total) are activated
        """
        # Arrange
        self._create_modules_for_all_profiles(empty_registry)
        service = DiscoveryService(registry=empty_registry)

        # Act
        assets = await service.run_discovery(discovery_context)

        # Assert
        sources = {asset.source for asset in assets}
        # STANDARD should activate 6 modules (2 quick + 4 standard)
        assert (
            5 <= len(sources) <= 7
        ), f"STANDARD profile should activate 5-7 modules, got {len(sources)}"
        # Should include quick modules
        assert "quick_only_1" in sources
        assert "quick_only_2" in sources
        # Should include standard modules
        for i in range(1, 5):
            assert f"standard_core_{i}" in sources, f"Missing standard_core_{i}"
        # Should NOT include full only modules
        for source in sources:
            assert not source.startswith(
                "full_only_"
            ), f"STANDARD should not activate {source}"

    @pytest.mark.asyncio
    async def test_full_profile_activates_all_modules(
        self,
        full_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """FULL profile should activate all modules (10).

        Given: Registry with 10 modules configured for different profiles
        When: DiscoveryService runs with FULL profile
        Then: All 10 modules are activated
        """
        # Arrange
        self._create_modules_for_all_profiles(empty_registry)
        service = DiscoveryService(registry=empty_registry)

        # Act
        assets = await service.run_discovery(full_context)

        # Assert
        sources = {asset.source for asset in assets}
        # FULL should activate all 10 modules
        assert (
            len(sources) == 10
        ), f"FULL profile should activate 10 modules, got {len(sources)}"
        # Should include all module types
        assert "quick_only_1" in sources
        assert "quick_only_2" in sources
        for i in range(1, 5):
            assert f"standard_core_{i}" in sources, f"Missing standard_core_{i}"
            assert f"full_only_{i}" in sources, f"Missing full_only_{i}"

    @pytest.mark.asyncio
    async def test_module_is_active_for_is_respected(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """DiscoveryService should respect module's is_active_for() result.

        Given: A module that only supports FULL profile
        When: DiscoveryService runs with STANDARD profile
        Then: The FULL-only module is NOT executed
        """
        # Arrange
        full_only_module = create_mock_module(
            name="full_exclusive",
            profiles={ScanProfile.FULL},
            assets=[
                create_test_asset(
                    "https://example.com/full", "endpoint", "full_exclusive"
                )
            ],
        )
        standard_module = create_mock_module(
            name="standard_supported",
            profiles={ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[
                create_test_asset(
                    "https://example.com/standard", "endpoint", "standard_supported"
                )
            ],
        )

        empty_registry.register(full_only_module)
        empty_registry.register(standard_module)

        service = DiscoveryService(registry=empty_registry)

        # Act
        assets = await service.run_discovery(discovery_context)

        # Assert
        sources = {asset.source for asset in assets}

        # Verify is_active_for behavior
        assert full_only_module.is_active_for(ScanProfile.FULL) is True
        assert full_only_module.is_active_for(ScanProfile.STANDARD) is False
        assert standard_module.is_active_for(ScanProfile.STANDARD) is True

        # FULL-only module should NOT be in results when running STANDARD profile
        assert (
            "full_exclusive" not in sources
        ), "FULL-only module should not run for STANDARD profile"
        assert "standard_supported" in sources, "STANDARD-compatible module should run"

        # Also verify call counts
        assert full_only_module.call_count == 0, "FULL-only module should not be called"
        assert standard_module.call_count == 1, "STANDARD module should be called once"
