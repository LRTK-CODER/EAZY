"""Integration test fixtures for Discovery module."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Set
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# Sample crawl data for testing
SAMPLE_CRAWL_DATA: Dict[str, Any] = {
    "http_data": {
        "https://example.com": {
            "request": {"method": "GET", "headers": {}, "body": ""},
            "response": {
                "status": 200,
                "headers": {"content-type": "text/html"},
                "body": "<html><body>Test</body></html>",
            },
        }
    },
    "html_content": "<html><head></head><body><a href='/page1'>Link</a></body></html>",
    "scripts": ["https://example.com/app.js"],
}


class MockDiscoveryModule(BaseDiscoveryModule):
    """Mock Discovery module for testing."""

    def __init__(
        self,
        name: str,
        profiles: Set[ScanProfile],
        assets: List[DiscoveredAsset] | None = None,
        delay: float = 0.0,
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._profiles = profiles
        self._assets = assets or []
        self._delay = delay
        self._should_fail = should_fail
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def profiles(self) -> Set[ScanProfile]:
        return self._profiles

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        import asyncio

        self.call_count += 1

        if self._delay > 0:
            await asyncio.sleep(self._delay)

        if self._should_fail:
            raise RuntimeError(f"Module {self._name} intentionally failed")

        for asset in self._assets:
            yield asset


def create_mock_module(
    name: str,
    profiles: Set[ScanProfile],
    assets: List[DiscoveredAsset] | None = None,
    delay: float = 0.0,
    should_fail: bool = False,
) -> MockDiscoveryModule:
    """Factory function to create mock modules."""
    return MockDiscoveryModule(
        name=name,
        profiles=profiles,
        assets=assets,
        delay=delay,
        should_fail=should_fail,
    )


def create_test_asset(
    url: str,
    asset_type: str = "endpoint",
    source: str = "test",
    metadata: Dict[str, Any] | None = None,
) -> DiscoveredAsset:
    """Factory function to create test assets."""
    return DiscoveredAsset(
        url=url,
        asset_type=asset_type,
        source=source,
        metadata=metadata or {},
    )


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client."""
    client = MagicMock()
    client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            headers={"content-type": "text/html"},
            text="<html></html>",
        )
    )
    client.post = AsyncMock(return_value=MagicMock(status_code=200))
    return client


@pytest.fixture
def empty_registry() -> DiscoveryModuleRegistry:
    """Empty registry for testing."""
    return DiscoveryModuleRegistry()


@pytest.fixture
def discovery_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Test DiscoveryContext with STANDARD profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.STANDARD,
        http_client=mock_http_client,
        crawl_data=SAMPLE_CRAWL_DATA,
    )


@pytest.fixture
def quick_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Test DiscoveryContext with QUICK profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.QUICK,
        http_client=mock_http_client,
        crawl_data=SAMPLE_CRAWL_DATA,
    )


@pytest.fixture
def full_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Test DiscoveryContext with FULL profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.FULL,
        http_client=mock_http_client,
        crawl_data=SAMPLE_CRAWL_DATA,
    )


@pytest.fixture
def sample_assets() -> List[DiscoveredAsset]:
    """Sample assets for testing."""
    return [
        create_test_asset("https://example.com/api/users", "endpoint", "module_a"),
        create_test_asset("https://example.com/api/posts", "endpoint", "module_a"),
        create_test_asset("https://example.com/login", "form", "module_b"),
        create_test_asset("https://example.com/static/app.js", "script", "module_c"),
    ]


@pytest.fixture
def duplicate_assets() -> List[DiscoveredAsset]:
    """Assets with duplicates for deduplication testing."""
    return [
        # Same URL and type from different sources - should be deduplicated
        create_test_asset("https://example.com/api/users", "endpoint", "module_a"),
        create_test_asset("https://example.com/api/users", "endpoint", "module_b"),
        create_test_asset("https://example.com/api/users", "endpoint", "module_c"),
        # Different URL - unique
        create_test_asset("https://example.com/api/posts", "endpoint", "module_a"),
        # Same URL but different type - unique
        create_test_asset("https://example.com/api/users", "form", "module_d"),
    ]
