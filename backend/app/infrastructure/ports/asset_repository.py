"""Asset repository port interface."""

from typing import Any, List, Optional, Protocol


class IAssetRepository(Protocol):
    """자산 저장소 인터페이스 - AssetService를 래핑"""

    async def save_batch(self, assets: List[Any], task_id: int) -> int:
        """
        자산 배치 저장.

        Args:
            assets: 저장할 자산 목록
            task_id: 연관 task ID

        Returns:
            저장된 자산 수
        """
        ...

    async def save_link(
        self,
        target_id: int,
        task_id: int,
        url: str,
        method: str,
        type: Any,
        source: Any,
        request_spec: Optional[Any] = None,
        response_spec: Optional[Any] = None,
        parameters: Optional[Any] = None,
    ) -> None:
        """
        개별 링크 저장.

        Args:
            target_id: Target ID
            task_id: Task ID
            url: Asset URL
            method: HTTP method
            type: Asset type
            source: Asset source
            request_spec: Request specification (optional)
            response_spec: Response specification (optional)
            parameters: Parameters (optional)
        """
        ...

    async def find_by_hash(self, content_hash: str) -> Optional[Any]:
        """해시로 자산 조회."""
        ...
