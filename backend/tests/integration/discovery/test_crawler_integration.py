"""Integration tests for Discovery crawler and profile-based module activation.

This module contains integration tests for:
- Profile-based module activation behavior
- DiscoveryService integration with DiscoveryModuleRegistry
- Module invocation and result collection
"""

from __future__ import annotations

import asyncio
import time
from typing import List
from unittest.mock import patch

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# TDD RED Phase: 아직 구현되지 않은 서비스 import
# 이 import는 DiscoveryService가 구현될 때까지 실패할 것입니다
from app.services.discovery.service import DiscoveryService
from tests.integration.discovery.conftest import create_mock_module, create_test_asset


class TestProfileBasedModuleActivation:
    """Tests for profile-based module activation behavior.

    Validates that modules are correctly activated based on the scan profile:
    - QUICK: Minimal modules (1 module - HtmlElementParser only)
    - STANDARD: Core modules (7 modules)
    - FULL: All modules (10 modules)
    """

    @pytest.fixture
    def all_modules_registry(self) -> DiscoveryModuleRegistry:
        """Create a registry with all 10 modules configured with proper profiles.

        Module distribution by profile:
        - QUICK: HtmlElementParser only (1 module)
        - STANDARD: 7 modules (including HtmlElementParser)
        - FULL: All 10 modules
        """
        registry = DiscoveryModuleRegistry()

        # QUICK profile module (1 module)
        # This module is active for all profiles
        registry.register(
            create_mock_module(
                name="HtmlElementParser",
                profiles={ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL},
            )
        )

        # STANDARD profile modules (6 additional modules, total 7 with HtmlElementParser)
        standard_module_names = [
            "NetworkAnalyzer",
            "JavaScriptParser",
            "FormDetector",
            "LinkExtractor",
            "MetadataCollector",
            "RobotsTxtParser",
        ]
        for name in standard_module_names:
            registry.register(
                create_mock_module(
                    name=name,
                    profiles={ScanProfile.STANDARD, ScanProfile.FULL},
                )
            )

        # FULL profile only modules (3 additional modules, total 10)
        full_only_module_names = [
            "DeepCrawler",
            "ApiEndpointDiscoverer",
            "SecurityHeaderAnalyzer",
        ]
        for name in full_only_module_names:
            registry.register(
                create_mock_module(
                    name=name,
                    profiles={ScanProfile.FULL},
                )
            )

        return registry

    def test_quick_profile_activates_minimal_modules(
        self,
        all_modules_registry: DiscoveryModuleRegistry,
        quick_context: DiscoveryContext,
    ) -> None:
        """QUICK profile should activate only minimal modules (1 module).

        The QUICK profile is designed for fast scans and should only include
        the HtmlElementParser module for basic HTML parsing.
        """
        active_modules = all_modules_registry.get_by_profile(ScanProfile.QUICK)

        # QUICK should have exactly 1 module
        assert len(active_modules) == 1

        # The only active module should be HtmlElementParser
        module_names = {m.name for m in active_modules}
        assert module_names == {"HtmlElementParser"}

    def test_standard_profile_activates_core_modules(
        self,
        all_modules_registry: DiscoveryModuleRegistry,
        discovery_context: DiscoveryContext,
    ) -> None:
        """STANDARD profile should activate core modules (7 modules).

        The STANDARD profile includes the HtmlElementParser plus 6 additional
        core modules for a balanced scan.
        """
        active_modules = all_modules_registry.get_by_profile(ScanProfile.STANDARD)

        # STANDARD should have exactly 7 modules
        assert len(active_modules) == 7

        # Verify expected modules are present
        module_names = {m.name for m in active_modules}
        expected_modules = {
            "HtmlElementParser",
            "NetworkAnalyzer",
            "JavaScriptParser",
            "FormDetector",
            "LinkExtractor",
            "MetadataCollector",
            "RobotsTxtParser",
        }
        assert module_names == expected_modules

    def test_full_profile_activates_all_modules(
        self,
        all_modules_registry: DiscoveryModuleRegistry,
        full_context: DiscoveryContext,
    ) -> None:
        """FULL profile should activate all modules (10 modules).

        The FULL profile includes all available modules for comprehensive
        scanning including deep crawling and security analysis.
        """
        active_modules = all_modules_registry.get_by_profile(ScanProfile.FULL)

        # FULL should have all 10 modules
        assert len(active_modules) == 10

        # Verify all expected modules are present
        module_names = {m.name for m in active_modules}
        expected_modules = {
            # QUICK module
            "HtmlElementParser",
            # STANDARD modules
            "NetworkAnalyzer",
            "JavaScriptParser",
            "FormDetector",
            "LinkExtractor",
            "MetadataCollector",
            "RobotsTxtParser",
            # FULL only modules
            "DeepCrawler",
            "ApiEndpointDiscoverer",
            "SecurityHeaderAnalyzer",
        }
        assert module_names == expected_modules

    def test_module_is_active_for_is_respected(
        self,
        all_modules_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Verify that is_active_for() result is properly respected by registry.

        Each module's is_active_for() method determines whether it should be
        activated for a given profile. The registry should correctly filter
        modules based on this method.
        """
        # Create a module that only supports FULL profile
        full_only_module = create_mock_module(
            name="FullOnlyTestModule",
            profiles={ScanProfile.FULL},
        )

        # Verify is_active_for returns correct values
        assert full_only_module.is_active_for(ScanProfile.QUICK) is False
        assert full_only_module.is_active_for(ScanProfile.STANDARD) is False
        assert full_only_module.is_active_for(ScanProfile.FULL) is True

        # Create a module that supports all profiles
        all_profiles_module = create_mock_module(
            name="AllProfilesTestModule",
            profiles={ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL},
        )

        # Verify is_active_for returns True for all profiles
        assert all_profiles_module.is_active_for(ScanProfile.QUICK) is True
        assert all_profiles_module.is_active_for(ScanProfile.STANDARD) is True
        assert all_profiles_module.is_active_for(ScanProfile.FULL) is True

        # Verify registry uses is_active_for correctly
        test_registry = DiscoveryModuleRegistry()
        test_registry.register(full_only_module)
        test_registry.register(all_profiles_module)

        # QUICK profile should only get all_profiles_module
        quick_modules = test_registry.get_by_profile(ScanProfile.QUICK)
        assert len(quick_modules) == 1
        assert quick_modules[0].name == "AllProfilesTestModule"

        # FULL profile should get both modules
        full_modules = test_registry.get_by_profile(ScanProfile.FULL)
        assert len(full_modules) == 2
        module_names = {m.name for m in full_modules}
        assert module_names == {"FullOnlyTestModule", "AllProfilesTestModule"}


class TestParallelModuleExecution:
    """Tests for parallel module execution in DiscoveryService.

    Validates that independent modules run concurrently using asyncio.gather
    for optimized execution time.
    """

    @pytest.mark.asyncio
    async def test_independent_modules_run_in_parallel(
        self, discovery_context: DiscoveryContext
    ) -> None:
        """Independent modules should run in parallel, not sequentially.

        Given: 3 modules each with 0.1s delay
        When: DiscoveryService runs all modules
        Then: Total execution time should be ~0.1s (parallel), not ~0.3s (sequential)
        """
        # Arrange
        registry = DiscoveryModuleRegistry()

        # Create 3 independent modules, each with 0.1s delay
        module_a = create_mock_module(
            name="module_a",
            profiles={ScanProfile.STANDARD},
            assets=[create_test_asset("https://example.com/a", "endpoint", "module_a")],
            delay=0.1,
        )
        module_b = create_mock_module(
            name="module_b",
            profiles={ScanProfile.STANDARD},
            assets=[create_test_asset("https://example.com/b", "endpoint", "module_b")],
            delay=0.1,
        )
        module_c = create_mock_module(
            name="module_c",
            profiles={ScanProfile.STANDARD},
            assets=[create_test_asset("https://example.com/c", "endpoint", "module_c")],
            delay=0.1,
        )

        registry.register(module_a)
        registry.register(module_b)
        registry.register(module_c)

        service = DiscoveryService(registry=registry)

        # Act
        start_time = time.monotonic()
        results: List[DiscoveredAsset] = await service.run(discovery_context)
        elapsed_time = time.monotonic() - start_time

        # Assert
        # All 3 modules should have been called
        assert module_a.call_count == 1
        assert module_b.call_count == 1
        assert module_c.call_count == 1

        # Should have 3 assets (one from each module)
        assert len(results) == 3

        # Parallel execution: should take ~0.1s, not ~0.3s
        # Allow some margin for test environment variance
        assert elapsed_time < 0.15, (
            f"Expected parallel execution (~0.1s) but took {elapsed_time:.3f}s. "
            "Modules may be running sequentially instead of in parallel."
        )

    @pytest.mark.asyncio
    async def test_asyncio_gather_is_used(
        self, discovery_context: DiscoveryContext
    ) -> None:
        """asyncio.gather should be used for parallel module execution.

        Given: A DiscoveryService with multiple modules
        When: Service runs modules
        Then: asyncio.gather should be called to run modules concurrently
        """
        # Arrange
        registry = DiscoveryModuleRegistry()

        module_a = create_mock_module(
            name="module_a",
            profiles={ScanProfile.STANDARD},
            assets=[create_test_asset("https://example.com/a", "endpoint", "module_a")],
        )
        module_b = create_mock_module(
            name="module_b",
            profiles={ScanProfile.STANDARD},
            assets=[create_test_asset("https://example.com/b", "endpoint", "module_b")],
        )

        registry.register(module_a)
        registry.register(module_b)

        service = DiscoveryService(registry=registry)

        # Act & Assert
        with patch("asyncio.gather", wraps=asyncio.gather) as mock_gather:
            await service.run(discovery_context)

            # asyncio.gather should have been called at least once
            assert mock_gather.called, (
                "asyncio.gather was not called. "
                "Modules should be executed in parallel using asyncio.gather."
            )

    @pytest.mark.asyncio
    async def test_execution_time_is_optimized(
        self, discovery_context: DiscoveryContext
    ) -> None:
        """Parallel execution should be faster than sequential execution.

        Given: 3 modules each with 0.1s delay
        When: Comparing parallel vs sequential execution
        Then: Parallel execution should be significantly faster
        """
        # Arrange
        registry = DiscoveryModuleRegistry()

        delay_per_module = 0.1
        num_modules = 3

        for i in range(num_modules):
            module = create_mock_module(
                name=f"module_{i}",
                profiles={ScanProfile.STANDARD},
                assets=[
                    create_test_asset(
                        f"https://example.com/{i}", "endpoint", f"module_{i}"
                    )
                ],
                delay=delay_per_module,
            )
            registry.register(module)

        service = DiscoveryService(registry=registry)

        # Calculate expected times
        sequential_time = delay_per_module * num_modules  # 0.3s
        parallel_time_max = delay_per_module + 0.05  # 0.15s (with margin)

        # Act
        start_time = time.monotonic()
        results: List[DiscoveredAsset] = await service.run(discovery_context)
        actual_time = time.monotonic() - start_time

        # Assert
        assert (
            len(results) == num_modules
        ), f"Expected {num_modules} results but got {len(results)}"

        # Execution should be optimized (parallel), not sequential
        assert actual_time < parallel_time_max, (
            f"Execution took {actual_time:.3f}s, which is too slow. "
            f"Expected < {parallel_time_max:.3f}s (parallel), "
            f"not ~{sequential_time:.3f}s (sequential)."
        )

        # Verify it's significantly faster than sequential would be
        assert actual_time < sequential_time * 0.7, (
            f"Execution time {actual_time:.3f}s is not significantly faster "
            f"than sequential time {sequential_time:.3f}s. "
            "Parallel execution optimization may not be working correctly."
        )


class TestDiscoveryModuleIntegration:
    """Tests for Discovery module integration with DiscoveryService.

    Validates the integration between DiscoveryService and DiscoveryModuleRegistry:
    - All registered modules are invoked during discovery
    - Results from all modules are collected and aggregated
    - Discovery results are properly passed to the next stage
    - Module execution is orchestrated correctly by the service
    """

    @pytest.mark.asyncio
    async def test_all_registered_modules_are_invoked(
        self,
        empty_registry: DiscoveryModuleRegistry,
        discovery_context: DiscoveryContext,
    ) -> None:
        """All registered modules should be invoked during discovery execution.

        Given: A registry with multiple modules registered for the current profile
        When: DiscoveryService.run_discovery() is called
        Then: Each registered module's discover() method should be called exactly once
        """
        # Arrange
        module_a = create_mock_module(
            name="ModuleA",
            profiles={ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[create_test_asset("https://example.com/a", "endpoint", "ModuleA")],
        )
        module_b = create_mock_module(
            name="ModuleB",
            profiles={ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[create_test_asset("https://example.com/b", "endpoint", "ModuleB")],
        )
        module_c = create_mock_module(
            name="ModuleC",
            profiles={ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[create_test_asset("https://example.com/c", "endpoint", "ModuleC")],
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)
        empty_registry.register(module_c)

        service = DiscoveryService(registry=empty_registry)

        # Act
        await service.run_discovery(discovery_context)

        # Assert - Each module should be called exactly once
        assert (
            module_a.call_count == 1
        ), f"ModuleA was called {module_a.call_count} times, expected 1"
        assert (
            module_b.call_count == 1
        ), f"ModuleB was called {module_b.call_count} times, expected 1"
        assert (
            module_c.call_count == 1
        ), f"ModuleC was called {module_c.call_count} times, expected 1"

    @pytest.mark.asyncio
    async def test_results_from_all_modules_collected(
        self,
        empty_registry: DiscoveryModuleRegistry,
        discovery_context: DiscoveryContext,
    ) -> None:
        """Results from all modules should be collected and aggregated.

        Given: Multiple modules each returning different assets
        When: DiscoveryService.run_discovery() is called
        Then: All assets from all modules should be collected in the result
        """
        # Arrange
        assets_module_a = [
            create_test_asset("https://example.com/api/users", "endpoint", "ModuleA"),
            create_test_asset("https://example.com/api/posts", "endpoint", "ModuleA"),
        ]
        assets_module_b = [
            create_test_asset("https://example.com/login", "form", "ModuleB"),
        ]
        assets_module_c = [
            create_test_asset("https://example.com/static/app.js", "script", "ModuleC"),
            create_test_asset(
                "https://example.com/static/vendor.js", "script", "ModuleC"
            ),
            create_test_asset(
                "https://example.com/static/style.css", "stylesheet", "ModuleC"
            ),
        ]

        module_a = create_mock_module(
            name="ModuleA",
            profiles={ScanProfile.STANDARD},
            assets=assets_module_a,
        )
        module_b = create_mock_module(
            name="ModuleB",
            profiles={ScanProfile.STANDARD},
            assets=assets_module_b,
        )
        module_c = create_mock_module(
            name="ModuleC",
            profiles={ScanProfile.STANDARD},
            assets=assets_module_c,
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)
        empty_registry.register(module_c)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run_discovery(discovery_context)

        # Assert - Total assets should be sum of all module assets
        expected_total = (
            len(assets_module_a) + len(assets_module_b) + len(assets_module_c)
        )
        assert len(results) == expected_total, (
            f"Expected {expected_total} total assets, but got {len(results)}. "
            "Not all module results were collected."
        )

        # Verify assets from each module are present
        result_urls = {asset.url for asset in results}
        expected_urls = {
            "https://example.com/api/users",
            "https://example.com/api/posts",
            "https://example.com/login",
            "https://example.com/static/app.js",
            "https://example.com/static/vendor.js",
            "https://example.com/static/style.css",
        }
        assert result_urls == expected_urls, (
            f"Missing assets in results. Expected URLs: {expected_urls}, "
            f"Got: {result_urls}"
        )

    @pytest.mark.asyncio
    async def test_discovery_results_passed_to_next_stage(
        self,
        empty_registry: DiscoveryModuleRegistry,
        discovery_context: DiscoveryContext,
    ) -> None:
        """Discovery results should be properly structured for the next stage.

        Given: Modules that discover various assets
        When: DiscoveryService.run_discovery() completes
        Then: Results should be in the correct format for downstream processing
              (e.g., vulnerability scanning, reporting)
        """
        # Arrange
        module = create_mock_module(
            name="TestModule",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    url="https://example.com/api/v1/users",
                    asset_type="endpoint",
                    source="TestModule",
                    metadata={"method": "GET", "auth_required": True},
                ),
                create_test_asset(
                    url="https://example.com/admin/login",
                    asset_type="form",
                    source="TestModule",
                    metadata={"fields": ["username", "password"]},
                ),
            ],
        )

        empty_registry.register(module)
        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run_discovery(discovery_context)

        # Assert - Results should be a list of DiscoveredAsset objects
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 2, f"Expected 2 assets, got {len(results)}"

        # Each result should be a properly structured DiscoveredAsset
        for asset in results:
            assert isinstance(
                asset, DiscoveredAsset
            ), f"Expected DiscoveredAsset, got {type(asset)}"
            assert hasattr(asset, "url"), "Asset should have 'url' attribute"
            assert hasattr(
                asset, "asset_type"
            ), "Asset should have 'asset_type' attribute"
            assert hasattr(asset, "source"), "Asset should have 'source' attribute"
            assert hasattr(asset, "metadata"), "Asset should have 'metadata' attribute"

        # Verify metadata is preserved for downstream processing
        endpoint_asset = next((a for a in results if a.asset_type == "endpoint"), None)
        assert endpoint_asset is not None, "Endpoint asset not found"
        assert (
            endpoint_asset.metadata.get("method") == "GET"
        ), "Metadata should be preserved for next stage processing"
        assert (
            endpoint_asset.metadata.get("auth_required") is True
        ), "Metadata should contain auth information for security analysis"

        form_asset = next((a for a in results if a.asset_type == "form"), None)
        assert form_asset is not None, "Form asset not found"
        assert (
            "fields" in form_asset.metadata
        ), "Form metadata should contain field information"

    @pytest.mark.asyncio
    async def test_module_execution_orchestrated_correctly(
        self,
        empty_registry: DiscoveryModuleRegistry,
        discovery_context: DiscoveryContext,
    ) -> None:
        """Module execution should be orchestrated correctly by DiscoveryService.

        Given: Modules with different profiles and execution characteristics
        When: DiscoveryService.run_discovery() is called with a specific profile
        Then: Only modules matching the profile should be executed
              and their execution should be properly coordinated
        """
        # Arrange - Create modules with different profile configurations
        quick_only_module = create_mock_module(
            name="QuickOnlyModule",
            profiles={ScanProfile.QUICK},
            assets=[
                create_test_asset(
                    "https://example.com/quick", "endpoint", "QuickOnlyModule"
                )
            ],
        )
        standard_module = create_mock_module(
            name="StandardModule",
            profiles={ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[
                create_test_asset(
                    "https://example.com/standard", "endpoint", "StandardModule"
                )
            ],
        )
        full_only_module = create_mock_module(
            name="FullOnlyModule",
            profiles={ScanProfile.FULL},
            assets=[
                create_test_asset(
                    "https://example.com/full", "endpoint", "FullOnlyModule"
                )
            ],
        )
        all_profiles_module = create_mock_module(
            name="AllProfilesModule",
            profiles={ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL},
            assets=[
                create_test_asset(
                    "https://example.com/all", "endpoint", "AllProfilesModule"
                )
            ],
        )

        empty_registry.register(quick_only_module)
        empty_registry.register(standard_module)
        empty_registry.register(full_only_module)
        empty_registry.register(all_profiles_module)

        service = DiscoveryService(registry=empty_registry)

        # Act - Run discovery with STANDARD profile context
        results: List[DiscoveredAsset] = await service.run_discovery(discovery_context)

        # Assert - Only STANDARD-compatible modules should be executed
        # STANDARD profile should run: StandardModule, AllProfilesModule
        # Should NOT run: QuickOnlyModule (QUICK only), FullOnlyModule (FULL only)
        assert (
            quick_only_module.call_count == 0
        ), "QuickOnlyModule should not be called for STANDARD profile"
        assert (
            standard_module.call_count == 1
        ), "StandardModule should be called for STANDARD profile"
        assert (
            full_only_module.call_count == 0
        ), "FullOnlyModule should not be called for STANDARD profile"
        assert (
            all_profiles_module.call_count == 1
        ), "AllProfilesModule should be called for STANDARD profile"

        # Verify correct results are returned
        assert (
            len(results) == 2
        ), f"Expected 2 results (StandardModule + AllProfilesModule), got {len(results)}"
        result_urls = {asset.url for asset in results}
        expected_urls = {
            "https://example.com/standard",
            "https://example.com/all",
        }
        assert result_urls == expected_urls, (
            f"Expected URLs {expected_urls}, got {result_urls}. "
            "Module orchestration may not be respecting profile constraints."
        )
