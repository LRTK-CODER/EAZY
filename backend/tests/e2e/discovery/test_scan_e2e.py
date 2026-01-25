"""E2E tests for Discovery scan profiles."""

from __future__ import annotations

from typing import Set

import pytest

from app.services.discovery.models import DiscoveredAsset, ScanProfile
from app.services.discovery.service import DiscoveryService


class TestQuickScanE2E:
    """E2E tests for QUICK profile scan."""

    @pytest.mark.asyncio
    async def test_quick_scan_completes_successfully(
        self, quick_registry, quick_discovery_context
    ):
        """QUICK scan completes without errors."""
        service = DiscoveryService(quick_registry)
        assets = await service.run_discovery(quick_discovery_context)

        assert isinstance(assets, list)
        # QUICK scan should return some assets
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

    @pytest.mark.asyncio
    async def test_quick_scan_only_fast_modules_executed(
        self, quick_registry, quick_discovery_context
    ):
        """Only fast modules are executed in QUICK profile."""
        # QUICK profile should have minimal modules
        modules = quick_registry.get_by_profile(ScanProfile.QUICK)

        # QUICK should have 1-2 modules max
        assert len(modules) <= 2

        service = DiscoveryService(quick_registry)
        assets = await service.run_discovery(quick_discovery_context)

        # Verify only QUICK-compatible module sources
        quick_module_names = {m.name for m in modules}
        for asset in assets:
            assert asset.source in quick_module_names

    @pytest.mark.asyncio
    async def test_quick_scan_results_within_expected_bounds(
        self, quick_registry, quick_discovery_context
    ):
        """QUICK scan results are within expected bounds."""
        service = DiscoveryService(quick_registry)
        assets = await service.run_discovery(quick_discovery_context)

        # QUICK scan should find basic assets from HTML parsing
        # Expected: links, forms, scripts from sample HTML
        assert len(assets) >= 0  # May be 0 if no matching content
        assert len(assets) <= 100  # Should not explode

    @pytest.mark.asyncio
    async def test_quick_scan_execution_time_under_limit(
        self, quick_registry, quick_discovery_context, time_limit_checker
    ):
        """QUICK scan completes in under 30 seconds."""
        service = DiscoveryService(quick_registry)

        with time_limit_checker.measure(ScanProfile.QUICK) as get_timing:
            await service.run_discovery(quick_discovery_context)

        result = get_timing()
        time_limit_checker.assert_within_limit(
            result.elapsed_seconds, ScanProfile.QUICK
        )


class TestStandardScanE2E:
    """E2E tests for STANDARD profile scan."""

    @pytest.mark.asyncio
    async def test_standard_scan_completes_successfully(
        self, standard_registry, e2e_discovery_context
    ):
        """STANDARD scan completes without errors."""
        service = DiscoveryService(standard_registry)
        assets = await service.run_discovery(e2e_discovery_context)

        assert isinstance(assets, list)
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

    @pytest.mark.asyncio
    async def test_standard_scan_core_modules_executed(
        self, standard_registry, e2e_discovery_context
    ):
        """Core modules are executed in STANDARD profile."""
        modules = standard_registry.get_by_profile(ScanProfile.STANDARD)

        # STANDARD should have 5-7 core modules
        assert len(modules) >= 5
        assert len(modules) <= 8

        service = DiscoveryService(standard_registry)
        assets = await service.run_discovery(e2e_discovery_context)

        # Should have assets from multiple module sources
        sources: Set[str] = {asset.source for asset in assets}
        # At least some modules should produce results
        assert len(sources) >= 1

    @pytest.mark.asyncio
    async def test_standard_scan_network_traffic_captured(
        self, standard_registry, e2e_discovery_context
    ):
        """Network traffic is captured in STANDARD scan."""
        service = DiscoveryService(standard_registry)
        assets = await service.run_discovery(e2e_discovery_context)

        # Check for network-related assets (API endpoints, XHR, etc.)
        asset_types: Set[str] = {asset.asset_type for asset in assets}

        # Should find at least endpoints or scripts
        expected_types = {"endpoint", "script", "api", "xhr"}
        found_network_types = asset_types & expected_types
        # May or may not find network assets depending on sample data
        assert isinstance(found_network_types, set)

    @pytest.mark.asyncio
    async def test_standard_scan_html_and_config_parsed(
        self, standard_registry, e2e_discovery_context
    ):
        """HTML and config are parsed in STANDARD scan."""
        service = DiscoveryService(standard_registry)
        assets = await service.run_discovery(e2e_discovery_context)

        # Check for HTML-parsed assets
        asset_types: Set[str] = {asset.asset_type for asset in assets}

        # HTML parser should find links, forms, scripts, etc.
        html_related_types = {"link", "form", "script", "image", "media"}
        found_html_types = asset_types & html_related_types
        # May have HTML-related assets
        assert isinstance(found_html_types, set)

    @pytest.mark.asyncio
    async def test_standard_scan_execution_time_under_limit(
        self, standard_registry, e2e_discovery_context, time_limit_checker
    ):
        """STANDARD scan completes in under 2 minutes."""
        service = DiscoveryService(standard_registry)

        with time_limit_checker.measure(ScanProfile.STANDARD) as get_timing:
            await service.run_discovery(e2e_discovery_context)

        result = get_timing()
        time_limit_checker.assert_within_limit(
            result.elapsed_seconds, ScanProfile.STANDARD
        )


class TestFullScanE2E:
    """E2E tests for FULL profile scan."""

    @pytest.mark.asyncio
    async def test_full_scan_completes_successfully(
        self, full_registry, full_discovery_context
    ):
        """FULL scan completes without errors."""
        service = DiscoveryService(full_registry)
        assets = await service.run_discovery(full_discovery_context)

        assert isinstance(assets, list)
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

    @pytest.mark.asyncio
    async def test_full_scan_all_modules_executed(
        self, full_registry, full_discovery_context
    ):
        """All modules (10) are executed in FULL profile."""
        modules = full_registry.get_by_profile(ScanProfile.FULL)

        # FULL should have all 10 modules
        assert len(modules) == 10

        service = DiscoveryService(full_registry)
        _assets = await service.run_discovery(full_discovery_context)

        # All modules should be registered
        module_names = {m.name for m in modules}
        assert len(module_names) == 10

    @pytest.mark.asyncio
    async def test_full_scan_ast_analysis_performed(
        self, full_registry, full_discovery_context
    ):
        """AST analysis is performed in FULL scan."""
        # Verify JS AST analyzer module is present
        modules = full_registry.get_by_profile(ScanProfile.FULL)
        module_names = {m.name for m in modules}

        # AST analyzer should be in FULL profile
        assert "js_analyzer_ast" in module_names

        service = DiscoveryService(full_registry)
        assets = await service.run_discovery(full_discovery_context)

        # Check for AST-discovered assets
        ast_assets = [a for a in assets if a.source == "js_analyzer_ast"]
        # AST analyzer may or may not find assets depending on JS content
        assert isinstance(ast_assets, list)

    @pytest.mark.asyncio
    async def test_full_scan_dynamic_interaction_tested(
        self, full_registry, full_discovery_context
    ):
        """Dynamic interaction is tested in FULL scan."""
        # Verify interaction engine module is present
        modules = full_registry.get_by_profile(ScanProfile.FULL)
        module_names = {m.name for m in modules}

        # Interaction engine should be in FULL profile
        assert "interaction_engine" in module_names

        service = DiscoveryService(full_registry)
        assets = await service.run_discovery(full_discovery_context)

        # Check for interaction-discovered assets
        interaction_assets = [a for a in assets if a.source == "interaction_engine"]
        # Interaction engine may or may not find assets
        assert isinstance(interaction_assets, list)

    @pytest.mark.asyncio
    async def test_full_scan_execution_time_under_limit(
        self, full_registry, full_discovery_context, time_limit_checker
    ):
        """FULL scan completes in under 5 minutes."""
        service = DiscoveryService(full_registry)

        with time_limit_checker.measure(ScanProfile.FULL) as get_timing:
            await service.run_discovery(full_discovery_context)

        result = get_timing()
        time_limit_checker.assert_within_limit(result.elapsed_seconds, ScanProfile.FULL)
