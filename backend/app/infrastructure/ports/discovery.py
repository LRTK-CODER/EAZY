"""Discovery service port interface."""

from typing import List, Protocol

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext


class IDiscoveryService(Protocol):
    """
    Discovery 서비스 인터페이스.

    Note: 기존 DiscoveryService는 run() 메서드를 사용하므로
    어댑터가 run() → discover() 매핑을 수행합니다.
    """

    async def discover(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
        """
        자산 발견 수행.

        Args:
            context: Discovery 컨텍스트

        Returns:
            발견된 자산 목록
        """
        ...
