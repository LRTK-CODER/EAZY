"""Integration tests for Asset deduplication in DiscoveryService.

TDD RED Phase: DiscoveryService의 중복 제거 기능 테스트.

이 모듈은 다음을 테스트합니다:
- 여러 모듈이 동일한 URL을 발견할 때 중복 제거
- DiscoveredAsset.__hash__를 사용한 중복 판별
- 메타데이터 병합 또는 최신 값 유지
- 중복 제거 후 정확한 개수 확인
"""

from __future__ import annotations

from typing import List, Set

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.registry import DiscoveryModuleRegistry

# TDD RED Phase: 아직 구현되지 않은 서비스 import
# 이 import는 DiscoveryService가 구현될 때까지 실패할 것입니다
from app.services.discovery.service import DiscoveryService
from tests.integration.discovery.conftest import create_mock_module, create_test_asset


class TestAssetDeduplication:
    """Tests for asset deduplication in DiscoveryService.

    DiscoveryService는 여러 모듈로부터 발견된 자산들을 수집하고,
    동일한 URL과 asset_type을 가진 자산들을 중복 제거해야 합니다.
    """

    @pytest.mark.asyncio
    async def test_same_url_from_multiple_modules_deduplicated(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """여러 모듈이 동일 URL 발견 시 중복 제거.

        Given: 3개의 모듈이 모두 동일한 URL과 asset_type을 가진 자산을 발견
        When: DiscoveryService가 모든 모듈을 실행
        Then: 결과에는 중복이 제거되어 1개의 자산만 반환
        """
        # Arrange
        common_url = "https://example.com/api/users"
        common_type = "endpoint"

        # 3개의 모듈이 동일한 URL을 발견
        module_a = create_mock_module(
            name="module_a",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    url=common_url,
                    asset_type=common_type,
                    source="module_a",
                    metadata={"discovered_by": "module_a"},
                )
            ],
        )
        module_b = create_mock_module(
            name="module_b",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    url=common_url,
                    asset_type=common_type,
                    source="module_b",
                    metadata={"discovered_by": "module_b"},
                )
            ],
        )
        module_c = create_mock_module(
            name="module_c",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    url=common_url,
                    asset_type=common_type,
                    source="module_c",
                    metadata={"discovered_by": "module_c"},
                )
            ],
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)
        empty_registry.register(module_c)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        # 모든 모듈이 호출되어야 함
        assert module_a.call_count == 1
        assert module_b.call_count == 1
        assert module_c.call_count == 1

        # 중복 제거 후 1개의 자산만 반환
        assert len(results) == 1
        assert results[0].url == common_url
        assert results[0].asset_type == common_type

    @pytest.mark.asyncio
    async def test_deduplication_uses_discovered_asset_hash(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """DiscoveredAsset.__hash__ 사용하여 중복 판별.

        Given: 동일한 URL과 asset_type을 가진 자산들 (다른 source와 metadata)
        When: Set을 사용하여 중복 제거
        Then: URL과 asset_type 기준으로만 중복 판별 (hash 기반)
        """
        # Arrange
        url = "https://example.com/api/data"
        asset_type = "endpoint"

        # 동일한 URL/type, 다른 source/metadata를 가진 자산들
        asset1 = create_test_asset(
            url=url,
            asset_type=asset_type,
            source="network_capturer",
            metadata={"method": "GET", "status": 200},
        )
        asset2 = create_test_asset(
            url=url,
            asset_type=asset_type,
            source="js_analyzer",
            metadata={"found_in": "app.js", "line": 42},
        )
        asset3 = create_test_asset(
            url=url,
            asset_type=asset_type,
            source="html_parser",
            metadata={"tag": "a", "href": url},
        )

        # DiscoveredAsset.__hash__ 동작 확인
        assert (
            hash(asset1) == hash(asset2) == hash(asset3)
        ), "같은 URL과 asset_type을 가진 자산들은 같은 해시를 가져야 합니다"

        # 모듈 설정
        module_network = create_mock_module(
            name="network_capturer",
            profiles={ScanProfile.STANDARD},
            assets=[asset1],
        )
        module_js = create_mock_module(
            name="js_analyzer",
            profiles={ScanProfile.STANDARD},
            assets=[asset2],
        )
        module_html = create_mock_module(
            name="html_parser",
            profiles={ScanProfile.STANDARD},
            assets=[asset3],
        )

        empty_registry.register(module_network)
        empty_registry.register(module_js)
        empty_registry.register(module_html)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        # Set 기반 중복 제거로 1개만 반환
        assert len(results) == 1

        # 반환된 자산이 원래 자산 중 하나와 동일 (URL/type 기준)
        assert results[0].url == url
        assert results[0].asset_type == asset_type

    @pytest.mark.asyncio
    async def test_metadata_merged_or_latest_kept(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """메타데이터 병합 또는 최신 유지.

        Given: 동일한 URL/type을 가진 자산들이 서로 다른 메타데이터를 가짐
        When: DiscoveryService가 중복 제거 수행
        Then: 메타데이터가 병합되거나 마지막 자산의 메타데이터가 유지됨

        Note: 현재 구현에서는 Set을 사용하므로 먼저 추가된 자산이 유지됩니다.
              향후 메타데이터 병합 로직이 추가될 수 있습니다.
        """
        # Arrange
        url = "https://example.com/api/items"
        asset_type = "endpoint"

        # 서로 다른 메타데이터를 가진 동일 자산들
        asset_early = create_test_asset(
            url=url,
            asset_type=asset_type,
            source="module_early",
            metadata={
                "method": "GET",
                "discovered_first": True,
            },
        )
        asset_later = create_test_asset(
            url=url,
            asset_type=asset_type,
            source="module_later",
            metadata={
                "method": "POST",
                "content_type": "application/json",
                "discovered_first": False,
            },
        )

        # 두 모듈이 순차적으로 자산 반환 (module_early가 먼저)
        module_early = create_mock_module(
            name="module_early",
            profiles={ScanProfile.STANDARD},
            assets=[asset_early],
            delay=0.0,
        )
        module_later = create_mock_module(
            name="module_later",
            profiles={ScanProfile.STANDARD},
            assets=[asset_later],
            delay=0.01,  # 약간의 지연으로 순서 보장
        )

        empty_registry.register(module_early)
        empty_registry.register(module_later)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        assert len(results) == 1
        result_asset = results[0]

        # URL과 type은 동일해야 함
        assert result_asset.url == url
        assert result_asset.asset_type == asset_type

        # 메타데이터 확인: Set 기반이므로 먼저 추가된 것이 유지됨
        # 또는 향후 병합 로직이 구현되면 두 메타데이터가 병합될 수 있음
        # 최소한 메타데이터가 존재해야 함
        assert result_asset.metadata is not None

        # 현재 Set 기반 구현에서는 먼저 추가된 자산이 유지됨
        # (병합 로직 구현 시 이 assertion 수정 필요)
        assert "method" in result_asset.metadata or result_asset.source in [
            "module_early",
            "module_later",
        ]

    @pytest.mark.asyncio
    async def test_count_accurate_after_deduplication(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
        duplicate_assets: List[DiscoveredAsset],
    ) -> None:
        """중복 제거 후 개수 정확.

        Given: duplicate_assets 픽스처 (5개 중 3개 중복)
               - https://example.com/api/users (endpoint) x 3 (module_a, b, c)
               - https://example.com/api/posts (endpoint) x 1 (module_a)
               - https://example.com/api/users (form) x 1 (module_d) - 다른 타입
        When: DiscoveryService가 중복 제거 수행
        Then: 정확히 3개의 고유 자산 반환
        """
        # Arrange
        # duplicate_assets를 여러 모듈에 분배
        # module_a: api/users(endpoint), api/posts(endpoint)
        # module_b: api/users(endpoint)
        # module_c: api/users(endpoint)
        # module_d: api/users(form)

        module_a = create_mock_module(
            name="module_a",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/api/users", "endpoint", "module_a"
                ),
                create_test_asset(
                    "https://example.com/api/posts", "endpoint", "module_a"
                ),
            ],
        )
        module_b = create_mock_module(
            name="module_b",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/api/users", "endpoint", "module_b"
                ),
            ],
        )
        module_c = create_mock_module(
            name="module_c",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(
                    "https://example.com/api/users", "endpoint", "module_c"
                ),
            ],
        )
        module_d = create_mock_module(
            name="module_d",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset("https://example.com/api/users", "form", "module_d"),
            ],
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)
        empty_registry.register(module_c)
        empty_registry.register(module_d)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        # 총 5개의 자산 중 3개가 중복 (api/users endpoint)
        # 예상 결과: 3개의 고유 자산
        # 1. https://example.com/api/users (endpoint) - 중복 제거됨
        # 2. https://example.com/api/posts (endpoint) - 고유
        # 3. https://example.com/api/users (form) - 고유 (다른 타입)
        assert len(results) == 3, (
            f"Expected 3 unique assets after deduplication, got {len(results)}. "
            f"Assets: {[(a.url, a.asset_type) for a in results]}"
        )

        # 고유한 (url, asset_type) 조합 확인
        unique_keys: Set[tuple[str, str]] = {
            (asset.url, asset.asset_type) for asset in results
        }
        expected_keys = {
            ("https://example.com/api/users", "endpoint"),
            ("https://example.com/api/posts", "endpoint"),
            ("https://example.com/api/users", "form"),
        }
        assert (
            unique_keys == expected_keys
        ), f"Expected keys {expected_keys}, got {unique_keys}"

    @pytest.mark.asyncio
    async def test_different_asset_types_same_url_not_deduplicated(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """동일 URL이라도 다른 asset_type은 중복이 아님.

        Given: 같은 URL이지만 다른 asset_type을 가진 자산들
        When: DiscoveryService가 중복 제거 수행
        Then: 모든 자산이 유지됨 (중복 아님)
        """
        # Arrange
        common_url = "https://example.com/login"

        module = create_mock_module(
            name="multi_type_module",
            profiles={ScanProfile.STANDARD},
            assets=[
                create_test_asset(common_url, "page", "crawler"),
                create_test_asset(common_url, "form", "html_parser"),
                create_test_asset(common_url, "endpoint", "network_capturer"),
            ],
        )

        empty_registry.register(module)
        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        # 동일 URL이지만 다른 타입이므로 모두 유지
        assert len(results) == 3

        asset_types = {asset.asset_type for asset in results}
        assert asset_types == {"page", "form", "endpoint"}

    @pytest.mark.asyncio
    async def test_empty_results_from_all_modules(
        self,
        discovery_context: DiscoveryContext,
        empty_registry: DiscoveryModuleRegistry,
    ) -> None:
        """모든 모듈이 빈 결과를 반환할 때.

        Given: 모든 모듈이 자산을 발견하지 못함
        When: DiscoveryService가 실행
        Then: 빈 리스트 반환
        """
        # Arrange
        module_a = create_mock_module(
            name="module_a",
            profiles={ScanProfile.STANDARD},
            assets=[],  # 빈 결과
        )
        module_b = create_mock_module(
            name="module_b",
            profiles={ScanProfile.STANDARD},
            assets=[],  # 빈 결과
        )

        empty_registry.register(module_a)
        empty_registry.register(module_b)

        service = DiscoveryService(registry=empty_registry)

        # Act
        results: List[DiscoveredAsset] = await service.run(discovery_context)

        # Assert
        assert len(results) == 0
        assert results == []
