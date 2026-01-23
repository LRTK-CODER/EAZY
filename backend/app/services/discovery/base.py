"""Discovery 모듈 기본 클래스.

모든 Discovery 모듈이 상속해야 하는 추상 기본 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Set

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile


class BaseDiscoveryModule(ABC):
    """Discovery 모듈 추상 기본 클래스.

    모든 Discovery 모듈은 이 클래스를 상속하고 추상 메서드를 구현해야 합니다.

    Subclass Requirements:
        - name: 모듈 고유 이름 (프로퍼티)
        - profiles: 지원하는 ScanProfile 집합 (프로퍼티)
        - discover: 자산 발견 로직 (async generator)

    Example:
        >>> class MyModule(BaseDiscoveryModule):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_module"
        ...
        ...     @property
        ...     def profiles(self) -> Set[ScanProfile]:
        ...         return {ScanProfile.STANDARD, ScanProfile.FULL}
        ...
        ...     async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveredAsset]:
        ...         yield DiscoveredAsset(url="...", asset_type="...", source=self.name)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """모듈 고유 이름."""
        ...

    @property
    @abstractmethod
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        ...

    @abstractmethod
    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        # yield is needed for type checker to recognize as async generator
        yield  # type: ignore

    def is_active_for(self, profile: ScanProfile) -> bool:
        """주어진 프로필에서 이 모듈이 활성화되는지 확인.

        Args:
            profile: 확인할 스캔 프로필

        Returns:
            프로필을 지원하면 True, 아니면 False
        """
        return profile in self.profiles
