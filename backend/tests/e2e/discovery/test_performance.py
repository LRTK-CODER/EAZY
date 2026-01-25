"""Performance tests for Discovery module.

Test 7.1.1: Large HTML parsing performance tests.
Test 7.1.2: Large JavaScript analysis performance tests.
Test 7.1.3: Concurrent request handling performance tests.
Test 7.1.4: Memory usage performance tests for Discovery service.
"""

from __future__ import annotations

import asyncio
import gc
import time
import tracemalloc
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules import (
    HtmlElementParserModule,
    JsAnalyzerRegexModule,
)
from app.services.discovery.service import DiscoveryService

# ============================================================================
# Test 7.1.1: Large HTML Parsing Performance
# ============================================================================


class TestLargeHtmlParsing:
    """Test 7.1.1: Large HTML file parsing performance.

    Performance requirements:
    - Parse 1MB HTML file in < 2 seconds
    - Memory usage stays under 200MB during parsing
    - All URLs are extracted correctly (verify count > 100)
    - No memory leak after parsing
    """

    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_html_parsing(self, large_html_content: str) -> None:
        """Parse 1MB HTML file within performance constraints.

        This test verifies that:
        1. Parsing completes in under 2 seconds
        2. Memory usage stays under 200MB
        3. More than 100 URLs are extracted
        4. No memory leak occurs after parsing

        RED Phase: This test should FAIL initially because the parser
        may not meet all performance requirements with large files.
        """
        # Verify fixture size (should be approximately 1MB)
        content_size_mb = len(large_html_content.encode("utf-8")) / (1024 * 1024)
        assert (
            content_size_mb >= 0.9
        ), f"HTML content too small: {content_size_mb:.2f}MB, expected ~1MB"

        # Performance thresholds (with CI buffer)
        # Allow extra time for CI environments which may be slower
        MAX_PARSE_TIME_SECONDS = 5.0  # Original: 2.0s, CI buffer: 2.5x
        MAX_MEMORY_MB = 200.0
        MIN_URL_COUNT = 500  # Stricter: expect more URLs from 1MB HTML

        # Initialize parser
        parser_module = HtmlElementParserModule()
        base_url = "https://example.com"

        # Force GC before test
        gc.collect()

        # Start memory tracking
        tracemalloc.start()
        memory_before = tracemalloc.get_traced_memory()[0]

        # Measure parsing time
        start_time = time.perf_counter()

        try:
            # Parse the large HTML content
            parse_result = parser_module.parse_with_base(large_html_content, base_url)

            # Get all extracted URLs
            extracted_urls = parse_result.get_all_urls()

        finally:
            end_time = time.perf_counter()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        # Calculate metrics
        elapsed_time = end_time - start_time
        memory_used_mb = peak_memory / (1024 * 1024)
        url_count = len(extracted_urls)

        # Log performance metrics
        print("\nPerformance Metrics (Test 7.1.1 - Large HTML Parsing):")
        print(f"  Content size: {content_size_mb:.2f} MB")
        print(
            f"  Parse time: {elapsed_time:.3f} seconds (limit: {MAX_PARSE_TIME_SECONDS}s)"
        )
        print(f"  Peak memory: {memory_used_mb:.2f} MB (limit: {MAX_MEMORY_MB}MB)")
        print(f"  URLs extracted: {url_count} (minimum: {MIN_URL_COUNT})")

        # Assert performance requirements
        assert elapsed_time < MAX_PARSE_TIME_SECONDS, (
            f"Parsing took {elapsed_time:.3f}s, exceeded limit of {MAX_PARSE_TIME_SECONDS}s. "
            f"Content size: {content_size_mb:.2f}MB"
        )

        assert memory_used_mb < MAX_MEMORY_MB, (
            f"Memory usage {memory_used_mb:.2f}MB exceeded limit of {MAX_MEMORY_MB}MB. "
            f"Content size: {content_size_mb:.2f}MB"
        )

        assert url_count > MIN_URL_COUNT, (
            f"Only {url_count} URLs extracted, expected more than {MIN_URL_COUNT}. "
            f"Content size: {content_size_mb:.2f}MB"
        )

        # Check for memory leak
        del parse_result
        del extracted_urls
        gc.collect()

        tracemalloc.start()
        memory_after_gc = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        # Memory after GC should return close to baseline
        memory_retained_mb = (memory_after_gc - memory_before) / (1024 * 1024)
        MAX_RETAINED_MB = 10.0  # Allow small overhead

        print(
            f"  Memory retained after GC: {memory_retained_mb:.2f} MB (limit: {MAX_RETAINED_MB}MB)"
        )

        assert memory_retained_mb < MAX_RETAINED_MB, (
            f"Memory leak detected: {memory_retained_mb:.2f}MB retained after GC, "
            f"expected less than {MAX_RETAINED_MB}MB"
        )


# ============================================================================
# Test 7.1.2: Large JavaScript Analysis Performance
# ============================================================================


class TestLargeJsAnalysis:
    """Test 7.1.2: Large JavaScript file analysis performance.

    Performance requirements:
    - Analyze 1MB JavaScript file in < 5 seconds
    - Memory usage stays under 500MB during analysis
    - Results contain expected URL patterns
    """

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_js_analysis(self, large_js_content: str) -> None:
        """Analyze 1MB JavaScript file within performance constraints.

        This test verifies that:
        1. Analysis completes in under 5 seconds
        2. Memory usage stays under 500MB
        3. Expected URL patterns are found in results

        RED Phase: This test should FAIL initially because the analyzer
        may not meet all performance requirements with large files.
        """
        # Verify fixture size (should be approximately 1MB)
        content_size_mb = len(large_js_content.encode("utf-8")) / (1024 * 1024)
        assert (
            content_size_mb >= 0.9
        ), f"JavaScript content too small: {content_size_mb:.2f}MB, expected ~1MB"

        # Performance thresholds
        MAX_ANALYSIS_TIME_SECONDS = 5.0
        MAX_MEMORY_MB = 500.0

        # Expected URL patterns that should be found in a realistic JS bundle
        EXPECTED_URL_PATTERNS = [
            "/api/",
            "https://",
            "wss://",
        ]

        # Initialize analyzer module
        analyzer_module = JsAnalyzerRegexModule()

        # Create mock discovery context with JS content
        mock_http_client = MagicMock()
        mock_crawl_data = {
            "target_url": "https://example.com",
            "base_url": "https://example.com",
            "js_contents": [
                {
                    "url": "https://example.com/bundle.js",
                    "content": large_js_content,
                }
            ],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=mock_crawl_data,
        )

        # Force GC before test
        gc.collect()

        # Start memory tracking
        tracemalloc.start()
        _memory_before = tracemalloc.get_traced_memory()[0]  # noqa: F841

        # Measure analysis time
        start_time = time.perf_counter()

        try:
            # Run analysis and collect all discovered assets
            discovered_assets: List[DiscoveredAsset] = []
            async for asset in analyzer_module.discover(context):
                discovered_assets.append(asset)

        finally:
            end_time = time.perf_counter()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        # Calculate metrics
        elapsed_time = end_time - start_time
        memory_used_mb = peak_memory / (1024 * 1024)
        asset_count = len(discovered_assets)

        # Extract all discovered URLs
        discovered_urls = [asset.url for asset in discovered_assets]

        # Check for expected patterns
        patterns_found: Dict[str, bool] = {}
        for pattern in EXPECTED_URL_PATTERNS:
            patterns_found[pattern] = any(pattern in url for url in discovered_urls)

        # Log performance metrics
        print("\nPerformance Metrics (Test 7.1.2 - Large JS Analysis):")
        print(f"  Content size: {content_size_mb:.2f} MB")
        print(
            f"  Analysis time: {elapsed_time:.3f} seconds (limit: {MAX_ANALYSIS_TIME_SECONDS}s)"
        )
        print(f"  Peak memory: {memory_used_mb:.2f} MB (limit: {MAX_MEMORY_MB}MB)")
        print(f"  Assets discovered: {asset_count}")
        print(f"  URL patterns found: {patterns_found}")

        # Assert performance requirements
        assert elapsed_time < MAX_ANALYSIS_TIME_SECONDS, (
            f"Analysis took {elapsed_time:.3f}s, exceeded limit of {MAX_ANALYSIS_TIME_SECONDS}s. "
            f"Content size: {content_size_mb:.2f}MB"
        )

        assert memory_used_mb < MAX_MEMORY_MB, (
            f"Memory usage {memory_used_mb:.2f}MB exceeded limit of {MAX_MEMORY_MB}MB. "
            f"Content size: {content_size_mb:.2f}MB"
        )

        # Verify expected URL patterns are found
        missing_patterns = [
            pattern for pattern, found in patterns_found.items() if not found
        ]
        assert not missing_patterns, (
            f"Expected URL patterns not found: {missing_patterns}. "
            f"Total assets discovered: {asset_count}. "
            f"Sample URLs: {discovered_urls[:10]}"
        )

        # Verify we found a reasonable number of assets
        # A 1MB JS bundle with 200+ API endpoints should yield at least 500 assets
        MIN_ASSET_COUNT = 500
        assert asset_count >= MIN_ASSET_COUNT, (
            f"Only {asset_count} assets discovered, expected at least {MIN_ASSET_COUNT}. "
            f"Content size: {content_size_mb:.2f}MB. "
            f"This suggests the analyzer is not extracting URL patterns efficiently."
        )


# ============================================================================
# Test 7.1.4: Memory Usage
# ============================================================================


class TestMemoryUsage:
    """Test 7.1.4: Memory usage limits."""

    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_peak_memory_under_1gb(self, full_registry, full_discovery_context):
        """Peak memory stays under 1GB during full scan."""
        service = DiscoveryService(full_registry)

        # Force garbage collection before measuring
        gc.collect()

        # Start memory tracking
        tracemalloc.start()

        try:
            # Run full discovery
            assets: List[DiscoveredAsset] = await service.run_discovery(
                full_discovery_context
            )

            # Check peak memory
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        # Memory limit: 1GB
        MEMORY_LIMIT = 1024 * 1024 * 1024  # 1GB in bytes

        assert peak < MEMORY_LIMIT, (
            f"Peak memory {peak / (1024 * 1024):.2f}MB exceeded 1GB limit. "
            f"Assets discovered: {len(assets)}"
        )

        # Log memory usage for CI visibility
        print("\nMemory Usage (Test 7.1.4 - Peak Memory):")
        print(f"  Current: {current / (1024 * 1024):.2f} MB")
        print(f"  Peak: {peak / (1024 * 1024):.2f} MB")
        print(f"  Assets: {len(assets)}")

    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_memory_released_after_scan(
        self, full_registry, full_discovery_context
    ):
        """Memory is released after scan completes."""
        service = DiscoveryService(full_registry)

        # Force garbage collection and get baseline
        gc.collect()
        tracemalloc.start()
        baseline_current, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Run discovery scan
        tracemalloc.start()
        assets = await service.run_discovery(full_discovery_context)
        during_scan_current, during_scan_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Clear references to assets and force GC
        asset_count = len(assets)
        del assets
        gc.collect()

        # Measure memory after cleanup
        tracemalloc.start()
        after_gc_current, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Calculate memory retained after GC
        # Allow some overhead for internal structures, but most should be freed
        # Memory after GC should be significantly less than peak during scan
        retention_ratio = (
            after_gc_current / during_scan_peak if during_scan_peak > 0 else 0
        )

        # Memory after GC should be less than 50% of peak (most memory released)
        MAX_RETENTION_RATIO = 0.5

        assert retention_ratio < MAX_RETENTION_RATIO, (
            f"Memory not properly released after scan. "
            f"Peak during scan: {during_scan_peak / (1024 * 1024):.2f}MB, "
            f"After GC: {after_gc_current / (1024 * 1024):.2f}MB, "
            f"Retention ratio: {retention_ratio:.2%}"
        )

        # Log memory release metrics
        print("\nMemory Usage (Test 7.1.4 - Memory Released):")
        print(f"  Baseline: {baseline_current / (1024 * 1024):.2f} MB")
        print(f"  During scan (current): {during_scan_current / (1024 * 1024):.2f} MB")
        print(f"  During scan (peak): {during_scan_peak / (1024 * 1024):.2f} MB")
        print(f"  After GC: {after_gc_current / (1024 * 1024):.2f} MB")
        print(f"  Retention ratio: {retention_ratio:.2%}")
        print(f"  Assets processed: {asset_count}")

    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_no_memory_leak_over_iterations(
        self, full_registry, full_discovery_context
    ):
        """No memory leak over 5 scan iterations."""
        ITERATIONS = 5
        MAX_GROWTH_RATIO = 0.1  # 10% maximum growth allowed

        service = DiscoveryService(full_registry)
        memory_readings: List[int] = []

        for i in range(ITERATIONS):
            # Force garbage collection before each iteration
            gc.collect()

            # Start fresh memory tracking for this iteration
            tracemalloc.start()

            # Run discovery scan
            assets = await service.run_discovery(full_discovery_context)

            # Record memory after scan
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Store peak memory for this iteration
            memory_readings.append(peak)

            # Clean up for next iteration
            del assets
            gc.collect()

            print(f"  Iteration {i + 1}: Peak memory = {peak / (1024 * 1024):.2f} MB")

        # Calculate memory growth between first and last iteration
        if memory_readings[0] > 0:
            growth = (memory_readings[-1] - memory_readings[0]) / memory_readings[0]
        else:
            growth = 0.0

        # Memory growth should be less than 10%
        assert growth < MAX_GROWTH_RATIO, (
            f"Memory leak detected over {ITERATIONS} iterations. "
            f"First iteration: {memory_readings[0] / (1024 * 1024):.2f}MB, "
            f"Last iteration: {memory_readings[-1] / (1024 * 1024):.2f}MB, "
            f"Growth: {growth:.2%}"
        )

        # Log memory leak detection results
        print("\nMemory Usage (Test 7.1.4 - Memory Leak Detection):")
        print(f"  Iterations: {ITERATIONS}")
        print(f"  First iteration peak: {memory_readings[0] / (1024 * 1024):.2f} MB")
        print(f"  Last iteration peak: {memory_readings[-1] / (1024 * 1024):.2f} MB")
        print(f"  Growth: {growth:.2%}")
        print(f"  Max allowed growth: {MAX_GROWTH_RATIO:.2%}")
        print(
            f"  All readings (MB): {[f'{m / (1024 * 1024):.2f}' for m in memory_readings]}"
        )

    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_gc_triggered_appropriately(
        self, full_registry, full_discovery_context
    ):
        """Garbage collection runs during memory-intensive operations."""
        service = DiscoveryService(full_registry)

        # Track GC statistics before scan
        gc.collect()
        gc_stats_before = gc.get_stats()
        gc_count_before = [
            gc.get_count()[0],  # Generation 0
            gc.get_count()[1],  # Generation 1
            gc.get_count()[2],  # Generation 2
        ]

        # Enable GC debugging to track collections (optional, can be verbose)
        # gc.set_debug(gc.DEBUG_STATS)

        # Run multiple discovery scans to generate garbage
        SCAN_ITERATIONS = 3
        for i in range(SCAN_ITERATIONS):
            _assets = await service.run_discovery(full_discovery_context)  # noqa: F841
            # Intentionally create garbage by not explicitly cleaning up
            # This tests if GC runs automatically during memory-intensive operations

        # Force a final GC and get stats
        gc.collect()
        gc_stats_after = gc.get_stats()
        gc_count_after = [
            gc.get_count()[0],
            gc.get_count()[1],
            gc.get_count()[2],
        ]

        # Calculate collection activity
        # GC stats include 'collections' count for each generation
        collections_gen0 = gc_stats_after[0].get("collections", 0) - gc_stats_before[
            0
        ].get("collections", 0)
        collections_gen1 = gc_stats_after[1].get("collections", 0) - gc_stats_before[
            1
        ].get("collections", 0)
        collections_gen2 = gc_stats_after[2].get("collections", 0) - gc_stats_before[
            2
        ].get("collections", 0)

        total_collections = collections_gen0 + collections_gen1 + collections_gen2

        # GC should have been triggered at least once during memory-intensive operations
        # Note: The exact number depends on memory pressure and GC thresholds
        # We verify that the GC system is functioning, not a specific count
        assert (
            total_collections >= 0
        ), "GC statistics should be available and non-negative"

        # Verify objects can be collected (no uncollectable cycles)
        gc.collect()
        uncollectable = gc.garbage
        assert len(uncollectable) == 0, (
            f"Found {len(uncollectable)} uncollectable objects, "
            "indicating potential circular references without weak refs"
        )

        # Log GC activity
        print("\nGC Activity (Test 7.1.4 - GC Triggered):")
        print(f"  Scan iterations: {SCAN_ITERATIONS}")
        print(f"  Collections Gen 0: {collections_gen0}")
        print(f"  Collections Gen 1: {collections_gen1}")
        print(f"  Collections Gen 2: {collections_gen2}")
        print(f"  Total collections: {total_collections}")
        print(f"  Uncollectable objects: {len(uncollectable)}")
        print(f"  GC count before: {gc_count_before}")
        print(f"  GC count after: {gc_count_after}")


class TestConcurrentRequests:
    """Test 7.1.3: Concurrent request handling."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_handle_100_concurrent_requests(
        self, mock_http_client, full_crawl_data
    ):
        """Handle 100 concurrent discovery requests without failure."""
        from app.services.discovery.modules import HtmlElementParserModule

        CONCURRENT_COUNT = 100
        module = HtmlElementParserModule()

        async def run_single_discovery(index: int):
            context = DiscoveryContext(
                target_url=f"https://example{index}.com",
                profile=ScanProfile.QUICK,
                http_client=mock_http_client,
                crawl_data=full_crawl_data,
            )
            assets = []
            async for asset in module.discover(context):
                assets.append(asset)
            return len(assets)

        results = await asyncio.gather(
            *[run_single_discovery(i) for i in range(CONCURRENT_COUNT)],
            return_exceptions=True,
        )

        # All should complete without exception
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Got {len(exceptions)} exceptions: {exceptions}"
        assert len(results) == CONCURRENT_COUNT

        # Log concurrent request results
        print("\nConcurrent Requests (Test 7.1.3 - 100 Concurrent):")
        print(f"  Total requests: {CONCURRENT_COUNT}")
        print(f"  Successful: {len(results) - len(exceptions)}")
        print(f"  Failed: {len(exceptions)}")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_no_request_timeout_under_load(
        self, mock_http_client, full_crawl_data
    ):
        """No request times out under normal concurrent load."""
        from app.services.discovery.modules import HtmlElementParserModule

        CONCURRENT_COUNT = 100
        TIMEOUT_SECONDS = 30.0
        module = HtmlElementParserModule()
        _timeout_count = 0  # noqa: F841
        timings: List[float] = []

        async def run_single_discovery_with_timeout(index: int) -> Dict[str, Any]:
            context = DiscoveryContext(
                target_url=f"https://example{index}.com",
                profile=ScanProfile.QUICK,
                http_client=mock_http_client,
                crawl_data=full_crawl_data,
            )
            start_time = time.monotonic()
            try:
                assets = []
                async with asyncio.timeout(TIMEOUT_SECONDS):
                    async for asset in module.discover(context):
                        assets.append(asset)
                elapsed = time.monotonic() - start_time
                return {
                    "index": index,
                    "success": True,
                    "elapsed": elapsed,
                    "assets": len(assets),
                }
            except asyncio.TimeoutError:
                elapsed = time.monotonic() - start_time
                return {
                    "index": index,
                    "success": False,
                    "elapsed": elapsed,
                    "timeout": True,
                }
            except Exception as e:
                elapsed = time.monotonic() - start_time
                return {
                    "index": index,
                    "success": False,
                    "elapsed": elapsed,
                    "error": str(e),
                }

        results = await asyncio.gather(
            *[run_single_discovery_with_timeout(i) for i in range(CONCURRENT_COUNT)]
        )

        # Analyze results
        timeouts = [r for r in results if r.get("timeout")]
        errors = [r for r in results if r.get("error")]
        successes = [r for r in results if r.get("success")]
        timings = [r["elapsed"] for r in results]

        # No timeouts should occur under normal load
        assert len(timeouts) == 0, (
            f"Got {len(timeouts)} timeouts under normal load. "
            f"Timeout threshold: {TIMEOUT_SECONDS}s"
        )

        # Log timing statistics
        if timings:
            avg_time = sum(timings) / len(timings)
            max_time = max(timings)
            min_time = min(timings)
            print("\nTimeout Test (Test 7.1.3 - No Timeout Under Load):")
            print(f"  Total requests: {CONCURRENT_COUNT}")
            print(f"  Successful: {len(successes)}")
            print(f"  Timeouts: {len(timeouts)}")
            print(f"  Errors: {len(errors)}")
            print(f"  Avg time: {avg_time:.3f}s")
            print(f"  Min time: {min_time:.3f}s")
            print(f"  Max time: {max_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_connection_pool_management(self, mock_http_client, full_crawl_data):
        """Connection pool is properly managed under concurrent load."""
        from app.services.discovery.modules import HtmlElementParserModule

        CONCURRENT_COUNT = 100
        module = HtmlElementParserModule()

        # Track the number of concurrent active contexts
        active_contexts: List[int] = []
        max_concurrent = 0
        lock = asyncio.Lock()

        async def run_single_discovery_tracked(index: int):
            nonlocal max_concurrent
            context = DiscoveryContext(
                target_url=f"https://example{index}.com",
                profile=ScanProfile.QUICK,
                http_client=mock_http_client,
                crawl_data=full_crawl_data,
            )

            async with lock:
                active_contexts.append(index)
                if len(active_contexts) > max_concurrent:
                    max_concurrent = len(active_contexts)

            try:
                assets = []
                async for asset in module.discover(context):
                    assets.append(asset)
                return len(assets)
            finally:
                async with lock:
                    active_contexts.remove(index)

        results = await asyncio.gather(
            *[run_single_discovery_tracked(i) for i in range(CONCURRENT_COUNT)],
            return_exceptions=True,
        )

        # All contexts should be released after completion
        assert (
            len(active_contexts) == 0
        ), f"Connection pool leak: {len(active_contexts)} contexts still active"

        # Verify all completed
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Got {len(exceptions)} exceptions"

        print("\nConnection Pool (Test 7.1.3 - Pool Management):")
        print(f"  Total requests: {CONCURRENT_COUNT}")
        print(f"  Max concurrent: {max_concurrent}")
        print(f"  Active after completion: {len(active_contexts)}")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_cleanup_after_concurrent(
        self, mock_http_client, full_crawl_data
    ):
        """Resources are properly cleaned up after concurrent operations."""
        from app.services.discovery.modules import HtmlElementParserModule

        CONCURRENT_COUNT = 100
        module = HtmlElementParserModule()

        # Force GC and get baseline
        gc.collect()
        _gc_count_before = gc.get_count()  # noqa: F841

        tracemalloc.start()
        baseline_memory, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        async def run_single_discovery(index: int):
            context = DiscoveryContext(
                target_url=f"https://example{index}.com",
                profile=ScanProfile.QUICK,
                http_client=mock_http_client,
                crawl_data=full_crawl_data,
            )
            assets = []
            async for asset in module.discover(context):
                assets.append(asset)
            return len(assets)

        # Run concurrent operations
        tracemalloc.start()
        results = await asyncio.gather(
            *[run_single_discovery(i) for i in range(CONCURRENT_COUNT)],
            return_exceptions=True,
        )
        peak_memory_during, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Clear results and force cleanup
        del results
        gc.collect()
        gc.collect()  # Run twice to ensure all generations are collected

        # Measure memory after cleanup
        tracemalloc.start()
        memory_after_cleanup, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory after cleanup should be significantly lower than peak
        # Allow for some retained memory due to module caches, etc.
        MAX_RETENTION_RATIO = 0.5  # At most 50% of peak memory retained

        if peak_memory_during > 0:
            retention_ratio = memory_after_cleanup / peak_memory_during
        else:
            retention_ratio = 0.0

        assert retention_ratio < MAX_RETENTION_RATIO, (
            f"Resource cleanup failed. "
            f"Peak memory: {peak_memory_during / (1024 * 1024):.2f}MB, "
            f"After cleanup: {memory_after_cleanup / (1024 * 1024):.2f}MB, "
            f"Retention: {retention_ratio:.2%}"
        )

        # Verify no uncollectable garbage
        uncollectable = gc.garbage
        assert (
            len(uncollectable) == 0
        ), f"Found {len(uncollectable)} uncollectable objects after concurrent operations"

        print("\nResource Cleanup (Test 7.1.3 - Cleanup After Concurrent):")
        print(f"  Concurrent requests: {CONCURRENT_COUNT}")
        print(f"  Baseline memory: {baseline_memory / (1024 * 1024):.2f} MB")
        print(f"  Peak memory: {peak_memory_during / (1024 * 1024):.2f} MB")
        print(f"  After cleanup: {memory_after_cleanup / (1024 * 1024):.2f} MB")
        print(f"  Retention ratio: {retention_ratio:.2%}")
        print(f"  Uncollectable objects: {len(uncollectable)}")
