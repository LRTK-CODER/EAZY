"""Discovery 서비스.

모든 Discovery 모듈을 조율하여 자산을 발견합니다.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Set

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext
from app.services.discovery.registry import DiscoveryModuleRegistry

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Discovery 서비스.

    레지스트리에 등록된 모듈들을 병렬로 실행하여 자산을 발견합니다.

    Features:
        - 프로필 기반 모듈 활성화
        - asyncio.gather를 사용한 병렬 실행
        - 에러 격리 (단일 모듈 실패 시 다른 모듈 계속 실행)
        - Set 기반 중복 제거
        - 모듈 간 의존성 지원

    Example:
        >>> registry = DiscoveryModuleRegistry()
        >>> registry.register(MyModule())
        >>> service = DiscoveryService(registry=registry)
        >>> assets = await service.run(context)
    """

    def __init__(
        self,
        registry: DiscoveryModuleRegistry,
        max_concurrency: int = 10,
    ) -> None:
        """DiscoveryService 초기화.

        Args:
            registry: Discovery 모듈 레지스트리
            max_concurrency: 최대 동시 실행 모듈 수 (기본 10)
        """
        self._registry = registry
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        # 의존성 그래프: dependent -> set of prerequisites
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, dependent: str, prerequisite: str) -> None:
        """모듈 간 의존성 추가.

        Args:
            dependent: 의존하는 모듈 이름
            prerequisite: 선행 모듈 이름
        """
        self._dependencies[dependent].add(prerequisite)

    async def run(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
        """Discovery 실행 (run_discovery의 별칭).

        Args:
            context: Discovery 실행 컨텍스트

        Returns:
            발견된 자산 리스트 (중복 제거됨)
        """
        return await self.run_discovery(context)

    async def run_discovery(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
        """Discovery 모듈을 실행하여 자산을 발견합니다.

        - context.profile에 따라 활성 모듈 선택
        - asyncio.gather로 병렬 실행
        - 에러 격리 (단일 모듈 실패 시 다른 모듈 계속 실행)
        - 중복 자산 제거 (Set 사용)
        - 에러 로깅

        Args:
            context: Discovery 실행 컨텍스트

        Returns:
            발견된 자산 리스트 (중복 제거됨)
        """
        # 프로필에 따른 활성 모듈 조회
        active_modules = self._registry.get_by_profile(context.profile)

        if not active_modules:
            return []

        # 의존성이 있는 모듈과 없는 모듈 분리
        modules_with_deps = {m for m in active_modules if m.name in self._dependencies}
        modules_without_deps = set(active_modules) - modules_with_deps

        # 중복 제거를 위한 Set
        discovered_assets: Set[DiscoveredAsset] = set()

        # 1단계: 의존성 없는 모듈 병렬 실행
        if modules_without_deps:
            tasks = [
                self._run_module_safe(module, context)
                for module in modules_without_deps
            ]
            results = await asyncio.gather(*tasks)

            for assets in results:
                discovered_assets.update(assets)

        # 2단계: 의존성 있는 모듈 순차 실행 (선행 모듈 완료 대기)
        for module in modules_with_deps:
            # 선행 모듈이 이미 실행된 경우에만 실행
            prereqs = self._dependencies.get(module.name, set())
            prereqs_completed = all(
                any(m.name == p for m in modules_without_deps) for p in prereqs
            )

            if prereqs_completed:
                assets = await self._run_module_safe(module, context)
                discovered_assets.update(assets)

        return list(discovered_assets)

    async def _run_module_safe(
        self,
        module: BaseDiscoveryModule,
        context: DiscoveryContext,
    ) -> List[DiscoveredAsset]:
        """단일 모듈을 안전하게 실행.

        에러 발생 시 로깅하고 빈 리스트 반환.

        Args:
            module: 실행할 모듈
            context: Discovery 컨텍스트

        Returns:
            발견된 자산 리스트 (에러 시 빈 리스트)
        """
        async with self._semaphore:
            try:
                assets: List[DiscoveredAsset] = []
                async for asset in module.discover(context):
                    assets.append(asset)
                return assets
            except Exception as e:
                logger.error(
                    f"Module '{module.name}' failed: {e}",
                    exc_info=True,
                )
                return []
