"""Integration tests for module error isolation in DiscoveryService.

This module contains integration tests for:
- Single module failure not crashing the entire scan
- Error logging with module name
- Other modules continuing execution after one fails
- Partial results being returned when some modules fail
"""

from __future__ import annotations

import logging
from typing import List

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# TDD RED Phase: Import the service that will be implemented
from app.services.discovery.service import DiscoveryService
from tests.integration.discovery.conftest import create_mock_module, create_test_asset


class TestModuleErrorIsolation:
    """Tests for module error isolation behavior in DiscoveryService.

    Validates that:
    - A single module failure does not crash the entire scan
    - Errors are logged with the module name for debugging
    - Other modules continue execution after one fails
    - Partial results from successful modules are returned
    """

    @pytest.mark.asyncio
    async def test_single_module_failure_doesnt_crash_scan(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """A single module failure should not crash the entire scan.

        Given: A registry with one failing module and one successful module
        When: DiscoveryService runs all modules
        Then: The scan completes without raising an exception
        """
        # Arrange
        failing_module = create_mock_module(
            name="failing_module",
            profiles={ScanProfile.STANDARD},
            should_fail=True,
        )
        successful_module = create_mock_module(
            name="successful_module",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/success",
                    "endpoint",
                    "successful_module",
                )
            ],
        )

        empty_registry.register(failing_module)
        empty_registry.register(successful_module)

        service = DiscoveryService(registry=empty_registry)

        # Act & Assert - should not raise an exception
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Verify scan completed and returned results from successful module
        assert results is not None
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_error_logged_with_module_name(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Errors should be logged with the module name for debugging.

        Given: A registry with a failing module
        When: DiscoveryService runs the module
        Then: The error is logged with the module name included
        """
        # Arrange
        failing_module = create_mock_module(
            name="failing_module",
            profiles={ScanProfile.STANDARD},
            should_fail=True,
        )

        empty_registry.register(failing_module)

        service = DiscoveryService(registry=empty_registry)

        # Act
        with caplog.at_level(logging.ERROR):
            await service.run(discovery_context)

        # Assert - error should be logged with module name
        assert len(caplog.records) >= 1, "Expected at least one error log record"

        # Find the error log related to the module failure
        module_error_logged = False
        for record in caplog.records:
            if "failing_module" in record.message:
                module_error_logged = True
                break

        assert module_error_logged, (
            "Expected error log to contain module name 'failing_module'. "
            f"Log messages: {[r.message for r in caplog.records]}"
        )

    @pytest.mark.asyncio
    async def test_other_modules_continue_execution(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Other modules should continue execution after one module fails.

        Given: A registry with one failing module and two successful modules
        When: DiscoveryService runs all modules
        Then: All modules are invoked (verified by call_count)
        """
        # Arrange
        failing_module = create_mock_module(
            name="failing_module",
            profiles={ScanProfile.STANDARD},
            should_fail=True,
        )
        successful_module_a = create_mock_module(
            name="successful_module_a",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/a",
                    "endpoint",
                    "successful_module_a",
                )
            ],
        )
        successful_module_b = create_mock_module(
            name="successful_module_b",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/b",
                    "endpoint",
                    "successful_module_b",
                )
            ],
        )

        empty_registry.register(failing_module)
        empty_registry.register(successful_module_a)
        empty_registry.register(successful_module_b)

        service = DiscoveryService(registry=empty_registry)

        # Act
        await service.run(discovery_context)

        # Assert - all modules should have been called
        assert failing_module.call_count == 1, (
            f"Expected failing_module to be called once, "
            f"but was called {failing_module.call_count} times"
        )
        assert successful_module_a.call_count == 1, (
            f"Expected successful_module_a to be called once, "
            f"but was called {successful_module_a.call_count} times"
        )
        assert successful_module_b.call_count == 1, (
            f"Expected successful_module_b to be called once, "
            f"but was called {successful_module_b.call_count} times"
        )

    @pytest.mark.asyncio
    async def test_partial_results_returned(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Partial results from successful modules should be returned.

        Given: A registry with one failing module and two successful modules
        When: DiscoveryService runs all modules
        Then: Results from successful modules are returned (failing module yields nothing)
        """
        # Arrange
        failing_module = create_mock_module(
            name="failing_module",
            profiles={ScanProfile.STANDARD},
            should_fail=True,
        )
        successful_module_a = create_mock_module(
            name="successful_module_a",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/a1",
                    "endpoint",
                    "successful_module_a",
                ),
                create_test_asset(
                    "https://example.com/a2",
                    "endpoint",
                    "successful_module_a",
                ),
            ],
        )
        successful_module_b = create_mock_module(
            name="successful_module_b",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/b1",
                    "form",
                    "successful_module_b",
                ),
            ],
        )

        empty_registry.register(failing_module)
        empty_registry.register(successful_module_a)
        empty_registry.register(successful_module_b)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert - should have 3 results (2 from module_a + 1 from module_b)
        assert len(results) == 3, (
            f"Expected 3 results from successful modules, but got {len(results)}. "
            "Partial results should be returned even when one module fails."
        )

        # Verify results contain expected URLs
        result_urls = {asset.url for asset in results}
        expected_urls = {
            "https://example.com/a1",
            "https://example.com/a2",
            "https://example.com/b1",
        }
        assert result_urls == expected_urls, (
            f"Expected URLs {expected_urls}, but got {result_urls}. "
            "Results from successful modules should be included."
        )

        # Verify results contain expected sources
        result_sources = {asset.source for asset in results}
        expected_sources = {"successful_module_a", "successful_module_b"}
        assert result_sources == expected_sources, (
            f"Expected sources {expected_sources}, but got {result_sources}. "
            "Results should only come from successful modules."
        )
