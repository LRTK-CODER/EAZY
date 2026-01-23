"""DiscoveryModuleRegistry 테스트.

TDD RED Phase: Registry 구현 전 실패해야 하는 테스트.
"""

from typing import Set

import pytest

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, ScanProfile


def create_mock_module(name: str, profiles: Set[ScanProfile]) -> BaseDiscoveryModule:
    """테스트용 모듈 생성 헬퍼."""

    class MockModule(BaseDiscoveryModule):
        def __init__(self, module_name: str, module_profiles: Set[ScanProfile]):
            self._name = module_name
            self._profiles = module_profiles

        @property
        def name(self) -> str:
            return self._name

        @property
        def profiles(self) -> Set[ScanProfile]:
            return self._profiles

        async def discover(self, context):
            yield DiscoveredAsset(
                url="https://example.com",
                asset_type="test",
                source=self._name,
            )

    return MockModule(name, profiles)


class TestRegistryRegister:
    """모듈 등록 테스트."""

    def test_can_register_module(self):
        """모듈 등록 가능."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module = create_mock_module("test_module", {ScanProfile.STANDARD})

        registry.register(module)

        # 등록 확인
        all_modules = registry.get_all()
        assert len(all_modules) == 1
        assert all_modules[0].name == "test_module"

    def test_register_multiple_modules(self):
        """여러 모듈 등록 가능."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module1 = create_mock_module("module1", {ScanProfile.QUICK})
        module2 = create_mock_module("module2", {ScanProfile.STANDARD})
        module3 = create_mock_module("module3", {ScanProfile.FULL})

        registry.register(module1)
        registry.register(module2)
        registry.register(module3)

        all_modules = registry.get_all()
        assert len(all_modules) == 3


class TestRegistryDuplicatePrevention:
    """중복 등록 방지 테스트."""

    def test_duplicate_name_raises_error(self):
        """같은 이름 모듈 중복 등록 시 에러."""
        from app.services.discovery.registry import (
            DiscoveryModuleRegistry,
            DuplicateModuleError,
        )

        registry = DiscoveryModuleRegistry()
        module1 = create_mock_module("same_name", {ScanProfile.QUICK})
        module2 = create_mock_module("same_name", {ScanProfile.STANDARD})

        registry.register(module1)

        with pytest.raises(DuplicateModuleError):
            registry.register(module2)

    def test_same_instance_raises_error(self):
        """같은 인스턴스 중복 등록 시 에러."""
        from app.services.discovery.registry import (
            DiscoveryModuleRegistry,
            DuplicateModuleError,
        )

        registry = DiscoveryModuleRegistry()
        module = create_mock_module("module", {ScanProfile.QUICK})

        registry.register(module)

        with pytest.raises(DuplicateModuleError):
            registry.register(module)


class TestRegistryGetByProfile:
    """프로필별 모듈 조회 테스트."""

    def test_get_modules_for_quick_profile(self):
        """QUICK 프로필 모듈 조회."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        quick_module = create_mock_module("quick", {ScanProfile.QUICK})
        standard_module = create_mock_module("standard", {ScanProfile.STANDARD})
        both_module = create_mock_module(
            "both", {ScanProfile.QUICK, ScanProfile.STANDARD}
        )

        registry.register(quick_module)
        registry.register(standard_module)
        registry.register(both_module)

        quick_modules = registry.get_by_profile(ScanProfile.QUICK)

        assert len(quick_modules) == 2
        names = [m.name for m in quick_modules]
        assert "quick" in names
        assert "both" in names
        assert "standard" not in names

    def test_get_modules_for_full_profile(self):
        """FULL 프로필 모듈 조회."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        full_module = create_mock_module("full", {ScanProfile.FULL})
        all_module = create_mock_module(
            "all", {ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL}
        )

        registry.register(full_module)
        registry.register(all_module)

        full_modules = registry.get_by_profile(ScanProfile.FULL)

        assert len(full_modules) == 2

    def test_returns_empty_for_no_matching(self):
        """매칭 모듈 없으면 빈 리스트."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        quick_module = create_mock_module("quick", {ScanProfile.QUICK})

        registry.register(quick_module)

        full_modules = registry.get_by_profile(ScanProfile.FULL)

        assert full_modules == []


class TestRegistryGetAll:
    """전체 모듈 조회 테스트."""

    def test_returns_all_registered_modules(self):
        """등록된 모든 모듈 반환."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module1 = create_mock_module("m1", {ScanProfile.QUICK})
        module2 = create_mock_module("m2", {ScanProfile.STANDARD})

        registry.register(module1)
        registry.register(module2)

        all_modules = registry.get_all()

        assert len(all_modules) == 2

    def test_returns_copy_not_reference(self):
        """원본이 아닌 복사본 반환."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module = create_mock_module("m1", {ScanProfile.QUICK})

        registry.register(module)

        all_modules = registry.get_all()
        all_modules.clear()  # 복사본 수정

        # 원본은 그대로
        assert len(registry.get_all()) == 1

    def test_empty_registry_returns_empty_list(self):
        """빈 레지스트리는 빈 리스트."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        all_modules = registry.get_all()

        assert all_modules == []


class TestRegistryGetByName:
    """이름으로 모듈 조회 테스트."""

    def test_get_existing_module_by_name(self):
        """존재하는 모듈 이름으로 조회."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module = create_mock_module("my_module", {ScanProfile.STANDARD})

        registry.register(module)

        found = registry.get_by_name("my_module")

        assert found is not None
        assert found.name == "my_module"

    def test_get_nonexistent_module_returns_none(self):
        """존재하지 않는 모듈은 None."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()

        found = registry.get_by_name("nonexistent")

        assert found is None


class TestRegistryClear:
    """레지스트리 초기화 테스트 (테스트용)."""

    def test_clear_removes_all_modules(self):
        """clear()로 모든 모듈 제거."""
        from app.services.discovery.registry import DiscoveryModuleRegistry

        registry = DiscoveryModuleRegistry()
        module = create_mock_module("m1", {ScanProfile.QUICK})

        registry.register(module)
        assert len(registry.get_all()) == 1

        registry.clear()

        assert len(registry.get_all()) == 0
