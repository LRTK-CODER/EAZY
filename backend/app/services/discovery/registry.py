"""Discovery 모듈 레지스트리.

Discovery 모듈의 등록 및 조회를 관리합니다.
"""

from typing import Dict, List, Optional

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import ScanProfile


class DuplicateModuleError(Exception):
    """모듈 중복 등록 에러."""

    pass


class DiscoveryModuleRegistry:
    """Discovery 모듈 레지스트리.

    모듈 등록, 프로필별 조회, 이름별 조회 기능을 제공합니다.

    Example:
        >>> registry = DiscoveryModuleRegistry()
        >>> registry.register(MyModule())
        >>> modules = registry.get_by_profile(ScanProfile.STANDARD)
    """

    def __init__(self) -> None:
        """레지스트리 초기화."""
        self._modules: Dict[str, BaseDiscoveryModule] = {}

    def register(self, module: BaseDiscoveryModule) -> None:
        """모듈을 레지스트리에 등록.

        Args:
            module: 등록할 Discovery 모듈

        Raises:
            DuplicateModuleError: 같은 이름의 모듈이 이미 등록된 경우
        """
        if module.name in self._modules:
            raise DuplicateModuleError(
                f"Module with name '{module.name}' is already registered"
            )
        self._modules[module.name] = module

    def get_by_profile(self, profile: ScanProfile) -> List[BaseDiscoveryModule]:
        """주어진 프로필을 지원하는 모듈 목록 반환.

        Args:
            profile: 스캔 프로필

        Returns:
            해당 프로필을 지원하는 모듈 리스트
        """
        return [m for m in self._modules.values() if m.is_active_for(profile)]

    def get_all(self) -> List[BaseDiscoveryModule]:
        """등록된 모든 모듈 반환.

        Returns:
            모든 등록된 모듈의 복사본 리스트
        """
        return list(self._modules.values())

    def get_by_name(self, name: str) -> Optional[BaseDiscoveryModule]:
        """이름으로 모듈 조회.

        Args:
            name: 모듈 이름

        Returns:
            해당 이름의 모듈 또는 None
        """
        return self._modules.get(name)

    def clear(self) -> None:
        """모든 등록된 모듈 제거 (테스트용)."""
        self._modules.clear()


def get_default_registry() -> DiscoveryModuleRegistry:
    """기본 Discovery 모듈 레지스트리 생성.

    모든 기본 모듈이 등록된 레지스트리를 반환합니다.
    Import는 함수 내부에서 수행하여 순환 참조를 방지합니다.

    Returns:
        기본 모듈이 등록된 DiscoveryModuleRegistry
    """
    from app.services.discovery.modules.config_discovery import ConfigDiscoveryModule
    from app.services.discovery.modules.html_element_parser import (
        HtmlElementParserModule,
    )
    from app.services.discovery.modules.js_analyzer_regex import JsAnalyzerRegexModule
    from app.services.discovery.modules.network_capturer import NetworkCapturerModule

    registry = DiscoveryModuleRegistry()
    registry.register(HtmlElementParserModule())
    registry.register(ConfigDiscoveryModule())
    registry.register(NetworkCapturerModule())
    registry.register(JsAnalyzerRegexModule())
    return registry
