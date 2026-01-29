"""AssetRepositoryAdapter - AssetService를 IAssetRepository 포트에 맞게 어댑팅."""

from typing import Any, List, Optional, cast

from app.models.asset import AssetSource, AssetType
from app.models.target import Target
from app.services.asset_service import AssetService


class AssetRepositoryAdapter:
    """AssetService를 IAssetRepository 포트에 맞게 어댑팅.

    discovered_assets를 Asset 모델로 변환하여 저장합니다.
    """

    def __init__(
        self,
        asset_service: AssetService,
        target: Target,
        transformer: Any,
    ):
        """AssetRepositoryAdapter 초기화.

        Args:
            asset_service: AssetService 인스턴스
            target: Target 객체 (id가 반드시 있어야 함)
            transformer: DataTransformer 인스턴스
        """
        self._asset_service = asset_service
        self._target = target
        self._target_id: int = cast(int, target.id)  # Target.id는 저장 후 항상 존재
        self._transformer = transformer

    async def save_batch(
        self,
        assets: List[Any],
        task_id: int,
        crawler_links: Optional[List[str]] = None,
        http_data: Any = None,
    ) -> int:
        """자산 배치 저장.

        Args:
            assets: 저장할 discovered asset 목록
            task_id: 연관 task ID
            crawler_links: 크롤러에서 발견한 링크 목록 (optional)
            http_data: HTTP 데이터 (optional)

        Returns:
            저장된 자산 수
        """
        saved_count = 0

        # 1. Save crawler links as assets (backward compatibility)
        if crawler_links and http_data:
            for link in crawler_links:
                link_http_data = http_data.get(link, {})
                request_data = link_http_data.get("request")
                response_data = link_http_data.get("response")
                parameters_data = link_http_data.get("parameters")

                http_method = (
                    request_data.get("method", "GET") if request_data else "GET"
                )

                await self._asset_service.process_asset(
                    target_id=self._target_id,
                    task_id=task_id,
                    url=link,
                    method=http_method,
                    type=AssetType.URL,
                    source=AssetSource.HTML,
                    request_spec=request_data,
                    response_spec=response_data,
                    parameters=parameters_data,
                )
                saved_count += 1

        # 2. Save discovered assets (from Discovery modules)
        for discovered in assets:
            # metadata에서 method 추출 (기본값 GET)
            method = discovered.metadata.get("method", "GET")

            # source 및 asset_type 매핑
            source = self._transformer.map_source(discovered.source)
            asset_type = self._transformer.map_type(discovered.asset_type)

            await self._asset_service.process_asset(
                target_id=self._target_id,
                task_id=task_id,
                url=discovered.url,
                method=method,
                type=asset_type,
                source=source,
            )
            saved_count += 1

        return saved_count

    async def save_individual(self, asset: Any, task_id: int) -> bool:
        """개별 자산 저장 (fallback).

        Args:
            asset: 저장할 asset
            task_id: Task ID

        Returns:
            True if saved successfully
        """
        try:
            method = asset.metadata.get("method", "GET")
            source = self._transformer.map_source(asset.source)
            asset_type = self._transformer.map_type(asset.asset_type)

            await self._asset_service.process_asset(
                target_id=self._target_id,
                task_id=task_id,
                url=asset.url,
                method=method,
                type=asset_type,
                source=source,
            )
            return True
        except Exception:
            return False

    async def save_link(
        self,
        target_id: int,
        task_id: int,
        url: str,
        method: str,
        type: AssetType,
        source: AssetSource,
        request_spec: Optional[Any] = None,
        response_spec: Optional[Any] = None,
        parameters: Optional[Any] = None,
    ) -> None:
        """개별 링크 저장.

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
        await self._asset_service.process_asset(
            target_id=target_id,
            task_id=task_id,
            url=url,
            method=method,
            type=type,
            source=source,
            request_spec=request_spec,
            response_spec=response_spec,
            parameters=parameters,
        )

    async def find_by_hash(self, content_hash: str) -> Optional[Any]:
        """해시로 자산 조회 (현재 미구현)."""
        return None
