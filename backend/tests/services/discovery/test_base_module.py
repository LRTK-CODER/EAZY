"""BaseDiscoveryModule ABC 테스트.

TDD RED Phase: BaseDiscoveryModule 구현 전 실패해야 하는 테스트.
"""

from typing import Set
from unittest.mock import MagicMock

import pytest


class TestBaseDiscoveryModuleStructure:
    """BaseDiscoveryModule 구조 테스트."""

    def test_is_abstract_base_class(self):
        """ABC인지 확인."""
        from abc import ABC

        from app.services.discovery.base import BaseDiscoveryModule

        assert issubclass(BaseDiscoveryModule, ABC)

    def test_has_name_abstract_property(self):
        """name 추상 프로퍼티 존재 확인."""
        from app.services.discovery.base import BaseDiscoveryModule

        assert hasattr(BaseDiscoveryModule, "name")
        # abstractproperty 확인
        assert getattr(BaseDiscoveryModule.name, "fget", None) is not None

    def test_has_profiles_abstract_property(self):
        """profiles 추상 프로퍼티 존재 확인."""
        from app.services.discovery.base import BaseDiscoveryModule

        assert hasattr(BaseDiscoveryModule, "profiles")

    def test_has_discover_abstract_method(self):
        """discover 추상 메서드 존재 확인."""

        from app.services.discovery.base import BaseDiscoveryModule

        assert hasattr(BaseDiscoveryModule, "discover")
        # 추상 메서드인지 확인
        assert getattr(BaseDiscoveryModule.discover, "__isabstractmethod__", False)


class TestBaseDiscoveryModuleCannotInstantiate:
    """추상 클래스 인스턴스화 불가 테스트."""

    def test_cannot_instantiate_directly(self):
        """직접 인스턴스화 불가."""
        from app.services.discovery.base import BaseDiscoveryModule

        with pytest.raises(TypeError):
            BaseDiscoveryModule()

    def test_cannot_instantiate_without_name(self):
        """name 없이 인스턴스화 불가."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import DiscoveredAsset, ScanProfile

        class IncompleteModule(BaseDiscoveryModule):
            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.QUICK}

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com",
                    asset_type="test",
                    source="test",
                )

        with pytest.raises(TypeError):
            IncompleteModule()

    def test_cannot_instantiate_without_profiles(self):
        """profiles 없이 인스턴스화 불가."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import DiscoveredAsset

        class IncompleteModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "incomplete"

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com",
                    asset_type="test",
                    source="test",
                )

        with pytest.raises(TypeError):
            IncompleteModule()

    def test_cannot_instantiate_without_discover(self):
        """discover 없이 인스턴스화 불가."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import ScanProfile

        class IncompleteModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.QUICK}

        with pytest.raises(TypeError):
            IncompleteModule()


class TestConcreteModule:
    """구체 구현 테스트."""

    def test_can_instantiate_complete_module(self):
        """완전한 모듈 인스턴스화 가능."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import DiscoveredAsset, ScanProfile

        class CompleteModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "complete"

            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.QUICK, ScanProfile.STANDARD}

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com",
                    asset_type="test",
                    source="test",
                )

        module = CompleteModule()
        assert module.name == "complete"
        assert ScanProfile.QUICK in module.profiles


class TestIsActiveFor:
    """is_active_for 메서드 테스트."""

    def test_returns_true_for_supported_profile(self):
        """지원하는 프로필에 True 반환."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import DiscoveredAsset, ScanProfile

        class QuickModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "quick_only"

            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.QUICK}

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com",
                    asset_type="test",
                    source="test",
                )

        module = QuickModule()
        assert module.is_active_for(ScanProfile.QUICK) is True

    def test_returns_false_for_unsupported_profile(self):
        """지원하지 않는 프로필에 False 반환."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import DiscoveredAsset, ScanProfile

        class QuickModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "quick_only"

            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.QUICK}

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com",
                    asset_type="test",
                    source="test",
                )

        module = QuickModule()
        assert module.is_active_for(ScanProfile.FULL) is False
        assert module.is_active_for(ScanProfile.STANDARD) is False


class TestDiscoverMethod:
    """discover 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_discover_returns_async_iterator(self):
        """discover가 AsyncIterator 반환."""
        from app.services.discovery.base import BaseDiscoveryModule
        from app.services.discovery.models import (
            DiscoveredAsset,
            DiscoveryContext,
            ScanProfile,
        )

        class TestModule(BaseDiscoveryModule):
            @property
            def name(self) -> str:
                return "test"

            @property
            def profiles(self) -> Set[ScanProfile]:
                return {ScanProfile.STANDARD}

            async def discover(self, context):
                yield DiscoveredAsset(
                    url="https://example.com/found",
                    asset_type="endpoint",
                    source="test",
                )

        module = TestModule()
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )

        assets = []
        async for asset in module.discover(context):
            assets.append(asset)

        assert len(assets) == 1
        assert assets[0].url == "https://example.com/found"
