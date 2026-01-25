"""Integration tests for parallel module execution in Discovery service.

This module contains TDD RED Phase tests for:
- Independent modules running in parallel
- asyncio.gather usage for parallelization
- Dependent modules waiting for prerequisites
- Execution time optimization

Test 6.1.5 - test_parallel_module_execution
"""

from __future__ import annotations

import asyncio
import time
from typing import List
from unittest.mock import patch

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# TDD RED Phase: Import DiscoveryService (not yet implemented)
from app.services.discovery.service import DiscoveryService
from tests.integration.discovery.conftest import create_mock_module, create_test_asset


class TestParallelModuleExecution:
    """Tests for parallel module execution in DiscoveryService.

    Validates that:
    1. Independent modules run concurrently using asyncio.gather
    2. Dependent modules wait for their prerequisites
    3. Execution time is optimized through parallelization
    """

    @pytest.mark.asyncio
    async def test_independent_modules_run_in_parallel(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Independent modules should run in parallel, not sequentially.

        Given: 5 independent modules each with 0.1s delay
        When: DiscoveryService runs all modules
        Then: Total execution time should be ~0.1s (parallel), not ~0.5s (sequential)

        This test verifies that modules without dependencies execute concurrently,
        resulting in execution time close to a single module's delay rather than
        the sum of all module delays.
        """
        # Arrange
        delay_per_module = 0.1
        num_modules = 5

        # Create 5 independent modules, each with 0.1s delay
        modules = []
        for i in range(num_modules):
            module = create_mock_module(
                name=f"independent_module_{i}",
                profiles={ScanProfile.STANDARD},
                assets=[
                    create_test_asset(
                        f"https://example.com/resource_{i}",
                        "endpoint",
                        f"independent_module_{i}",
                    )
                ],
                delay=delay_per_module,
            )
            empty_registry.register(module)
            modules.append(module)

        service = DiscoveryService(registry=empty_registry)

        # Act
        start = time.monotonic()
        results: List[DiscoveredAsset] = await service.run(discovery_context)
        duration = time.monotonic() - start

        # Assert
        # All modules should have been invoked exactly once
        for module in modules:
            assert (
                module.call_count == 1
            ), f"Module {module.name} was called {module.call_count} times, expected 1"

        # Should have collected assets from all modules
        assert (
            len(results) == num_modules
        ), f"Expected {num_modules} assets but got {len(results)}"

        # Parallel execution verification:
        # Sequential execution would take: 5 * 0.1s = 0.5s
        # Parallel execution should take: ~0.1s (+ small overhead)
        # We use 0.3s threshold (60% of sequential time) to confirm parallelism
        sequential_time = delay_per_module * num_modules  # 0.5s
        parallel_threshold = sequential_time * 0.6  # 0.3s

        assert duration < parallel_threshold, (
            f"Execution took {duration:.3f}s which suggests sequential execution. "
            f"Expected parallel execution to complete in < {parallel_threshold:.3f}s "
            f"(sequential would take ~{sequential_time:.3f}s). "
            "Verify that asyncio.gather is being used for parallelization."
        )

    @pytest.mark.asyncio
    async def test_asyncio_gather_used_for_parallelization(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """asyncio.gather should be used to parallelize module execution.

        Given: A DiscoveryService with multiple modules
        When: Service runs discovery modules
        Then: asyncio.gather should be called to run modules concurrently

        This test patches asyncio.gather to verify it is being used as the
        parallelization mechanism for independent module execution.
        """
        # Arrange
        module_a = create_mock_module(
            name="module_alpha",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/alpha", "endpoint", "module_alpha"
                )
            ],
        )
        module_b = create_mock_module(
            name="module_beta",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset("https://example.com/beta", "endpoint", "module_beta")
            ],
        )
        module_c = create_mock_module(
            name="module_gamma",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/gamma", "endpoint", "module_gamma"
                )
            ],
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)
        empty_registry.register(module_c)

        service = DiscoveryService(registry=empty_registry)

        # Act & Assert
        # Patch asyncio.gather with wraps to preserve functionality
        with patch("asyncio.gather", wraps=asyncio.gather) as mock_gather:
            _results = await service.run(discovery_context)

            # asyncio.gather must be called at least once for parallelization
            assert mock_gather.called, (
                "asyncio.gather was not called during module execution. "
                "Parallel module execution should use asyncio.gather to run "
                "independent modules concurrently."
            )

            # Verify gather was called with multiple coroutines
            call_args = mock_gather.call_args
            if call_args:
                # Check that gather received multiple items to parallelize
                args = call_args.args if call_args.args else []
                assert len(args) >= 2, (
                    f"asyncio.gather was called with only {len(args)} coroutine(s). "
                    "Expected multiple coroutines for parallel execution."
                )

    @pytest.mark.asyncio
    async def test_dependent_modules_wait_for_prerequisites(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Dependent modules should wait for their prerequisite modules to complete.

        Given: Module B depends on Module A's results
        When: DiscoveryService runs discovery
        Then: Module B should only execute after Module A completes

        This test verifies that the execution order respects module dependencies,
        ensuring that dependent modules receive the results they need from
        their prerequisites.
        """
        # Arrange
        execution_order: List[str] = []

        # Create a prerequisite module (Module A)
        module_a = create_mock_module(
            name="prerequisite_module_a",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/prerequisite_data",
                    "endpoint",
                    "prerequisite_module_a",
                )
            ],
            delay=0.1,
        )

        # Create a dependent module (Module B) that requires Module A
        module_b = create_mock_module(
            name="dependent_module_b",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/dependent_data",
                    "endpoint",
                    "dependent_module_b",
                )
            ],
            delay=0.05,
        )

        # Store original discover methods to track execution order
        original_discover_a = module_a.discover
        original_discover_b = module_b.discover

        async def tracked_discover_a(context):
            execution_order.append("module_a_start")
            async for asset in original_discover_a(context):
                yield asset
            execution_order.append("module_a_end")

        async def tracked_discover_b(context):
            execution_order.append("module_b_start")
            async for asset in original_discover_b(context):
                yield asset
            execution_order.append("module_b_end")

        # Monkey-patch the discover methods
        module_a.discover = tracked_discover_a
        module_b.discover = tracked_discover_b

        empty_registry.register(module_a)
        empty_registry.register(module_b)

        # Set up dependency: module_b depends on module_a
        # This assumes DiscoveryService supports a method to define dependencies
        service = DiscoveryService(registry=empty_registry)

        # Define dependency relationship
        # TDD RED Phase: This method signature is expected to exist
        service.add_dependency(
            dependent="dependent_module_b",
            prerequisite="prerequisite_module_a",
        )

        # Act
        _results = await service.run(discovery_context)

        # Assert
        # Module A should complete before Module B starts
        assert "module_a_end" in execution_order, "Module A should complete execution"
        assert "module_b_start" in execution_order, "Module B should start execution"

        a_end_index = execution_order.index("module_a_end")
        b_start_index = execution_order.index("module_b_start")

        assert a_end_index < b_start_index, (
            f"Dependent module B started at index {b_start_index} before "
            f"prerequisite module A completed at index {a_end_index}. "
            "Dependent modules must wait for their prerequisites to complete. "
            f"Execution order was: {execution_order}"
        )

    @pytest.mark.asyncio
    async def test_execution_time_optimized(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """Parallel execution should significantly reduce total execution time.

        Given: 5 modules each with 0.1s delay
        When: Running discovery with parallel execution
        Then: Total time should be optimized (close to single module time)

        This test quantitatively verifies that parallel execution provides
        meaningful performance optimization compared to sequential execution.
        """
        # Arrange
        delay_per_module = 0.1
        num_modules = 5

        for i in range(num_modules):
            module = create_mock_module(
                name=f"optimized_module_{i}",
                profiles={ScanProfile.STANDARD},
                assets=[
                    create_test_asset(
                        f"https://example.com/optimized_{i}",
                        "endpoint",
                        f"optimized_module_{i}",
                    )
                ],
                delay=delay_per_module,
            )
            empty_registry.register(module)

        service = DiscoveryService(registry=empty_registry)

        # Calculate expected times
        sequential_time = delay_per_module * num_modules  # 0.5s
        optimal_parallel_time = delay_per_module  # 0.1s (theoretical minimum)
        acceptable_parallel_time = delay_per_module * 1.5  # 0.15s (with overhead)

        # Act
        start = time.monotonic()
        results = await service.run(discovery_context)
        duration = time.monotonic() - start

        # Assert
        # Verify all modules produced results
        assert (
            len(results) == num_modules
        ), f"Expected {num_modules} results but got {len(results)}"

        # Primary assertion: execution time is optimized
        assert duration < acceptable_parallel_time, (
            f"Execution took {duration:.3f}s. "
            f"Expected optimized parallel execution to complete in < {acceptable_parallel_time:.3f}s. "
            f"Optimal parallel time is ~{optimal_parallel_time:.3f}s."
        )

        # Secondary assertion: significantly faster than sequential
        speedup_ratio = sequential_time / duration if duration > 0 else float("inf")
        min_expected_speedup = 3.0  # At least 3x faster than sequential

        assert speedup_ratio >= min_expected_speedup, (
            f"Speedup ratio is only {speedup_ratio:.2f}x. "
            f"Expected at least {min_expected_speedup}x speedup from parallel execution. "
            f"Sequential time: {sequential_time:.3f}s, Actual time: {duration:.3f}s. "
            "This suggests modules are not running in parallel efficiently."
        )

        # Tertiary assertion: not running sequentially
        assert duration < sequential_time * 0.5, (
            f"Execution time {duration:.3f}s is more than 50% of sequential time "
            f"({sequential_time:.3f}s). Parallel execution should provide better "
            "performance improvement."
        )
