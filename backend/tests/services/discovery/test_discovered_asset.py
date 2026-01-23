"""DiscoveredAsset 데이터 클래스 테스트.

TDD RED Phase: DiscoveredAsset 구현 전 실패해야 하는 테스트.
"""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest


class TestDiscoveredAssetCreation:
    """DiscoveredAsset 생성 테스트."""

    def test_create_with_required_fields(self):
        """필수 필드로 생성 가능한지 확인."""
        from app.services.discovery.models import DiscoveredAsset

        asset = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )

        assert asset.url == "https://example.com/api"
        assert asset.asset_type == "endpoint"
        assert asset.source == "network"

    def test_optional_fields_have_defaults(self):
        """선택적 필드에 기본값이 있는지 확인."""
        from app.services.discovery.models import DiscoveredAsset

        asset = DiscoveredAsset(
            url="https://example.com",
            asset_type="page",
            source="html",
        )

        assert asset.metadata == {}
        assert isinstance(asset.discovered_at, datetime)

    def test_can_set_metadata(self):
        """메타데이터 설정 가능한지 확인."""
        from app.services.discovery.models import DiscoveredAsset

        metadata = {"method": "POST", "content_type": "application/json"}
        asset = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
            metadata=metadata,
        )

        assert asset.metadata == metadata


class TestDiscoveredAssetImmutability:
    """불변성 테스트."""

    def test_cannot_modify_url(self):
        """URL 수정 시 에러 발생."""
        from app.services.discovery.models import DiscoveredAsset

        asset = DiscoveredAsset(
            url="https://example.com",
            asset_type="page",
            source="html",
        )

        with pytest.raises(FrozenInstanceError):
            asset.url = "https://other.com"

    def test_cannot_modify_asset_type(self):
        """asset_type 수정 시 에러 발생."""
        from app.services.discovery.models import DiscoveredAsset

        asset = DiscoveredAsset(
            url="https://example.com",
            asset_type="page",
            source="html",
        )

        with pytest.raises(FrozenInstanceError):
            asset.asset_type = "api"


class TestDiscoveredAssetHash:
    """해시 기능 테스트 (중복 제거용)."""

    def test_same_url_and_type_same_hash(self):
        """같은 URL과 타입은 같은 해시."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        asset2 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="html",  # 다른 source
        )

        assert hash(asset1) == hash(asset2)

    def test_different_url_different_hash(self):
        """다른 URL은 다른 해시."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        asset2 = DiscoveredAsset(
            url="https://example.com/other",
            asset_type="endpoint",
            source="network",
        )

        assert hash(asset1) != hash(asset2)

    def test_different_type_different_hash(self):
        """다른 타입은 다른 해시."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        asset2 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="form",
            source="network",
        )

        assert hash(asset1) != hash(asset2)

    def test_can_be_used_in_set(self):
        """set에서 사용 가능한지 확인."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        # 같은 URL/타입, 다른 메타데이터
        asset2 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="html",
            metadata={"extra": "data"},
        )
        asset3 = DiscoveredAsset(
            url="https://example.com/other",
            asset_type="endpoint",
            source="network",
        )

        asset_set = {asset1, asset2, asset3}

        # asset1과 asset2는 같은 것으로 처리 (중복 제거)
        assert len(asset_set) == 2


class TestDiscoveredAssetEquality:
    """동등성 비교 테스트."""

    def test_same_url_and_type_are_equal(self):
        """같은 URL과 타입은 동일."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        asset2 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="html",  # source는 다름
        )

        assert asset1 == asset2

    def test_different_url_not_equal(self):
        """다른 URL은 다름."""
        from app.services.discovery.models import DiscoveredAsset

        asset1 = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )
        asset2 = DiscoveredAsset(
            url="https://example.com/other",
            asset_type="endpoint",
            source="network",
        )

        assert asset1 != asset2

    def test_comparison_with_non_asset_returns_false(self):
        """다른 타입과 비교 시 False."""
        from app.services.discovery.models import DiscoveredAsset

        asset = DiscoveredAsset(
            url="https://example.com/api",
            asset_type="endpoint",
            source="network",
        )

        assert asset != "not an asset"
        assert asset != {"url": "https://example.com/api"}
        assert asset != None  # noqa: E711
