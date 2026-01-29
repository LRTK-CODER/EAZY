"""RecurseStage - 자식 Task 생성 Stage."""

import logging
from typing import Any, List, Set
from urllib.parse import urljoin

from app.application.stages.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


class RecurseStage(PipelineStage):
    """자식 Task 생성 Stage.

    크롤링에서 발견된 링크에 대해 자식 Task를 생성합니다.
    max_depth 제한, scope 검증, URL 중복 제거를 수행합니다.
    """

    def __init__(
        self,
        task_queue: Any,
        scope_checker: Any,
    ):
        """RecurseStage 초기화.

        Args:
            task_queue: ITaskQueue 호환 객체
            scope_checker: ScopeChecker 호환 객체
        """
        self._task_queue = task_queue
        self._scope_checker = scope_checker

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "recurse"

    async def process(self, context: Any) -> StageResult:
        """자식 Task 생성.

        Args:
            context: PipelineContext

        Returns:
            StageResult: 실행 결과
        """
        # 취소 확인
        if context.is_cancelled:
            return StageResult.stop("Task cancelled")

        # crawl_data 없으면 스킵
        if not context.crawl_data:
            context.set_child_tasks_spawned(0)
            return StageResult.ok()

        # max_depth 도달 시 스킵
        if context.depth >= context.max_depth:
            logger.debug(
                "Max depth reached: depth=%d, max_depth=%d",
                context.depth,
                context.max_depth,
            )
            context.set_child_tasks_spawned(0)
            return StageResult.ok()

        links = context.crawl_data.links
        if not links:
            context.set_child_tasks_spawned(0)
            return StageResult.ok()

        try:
            # URL 정규화 및 절대 URL 변환
            base_url = context.crawl_url
            normalized_links = self._normalize_and_deduplicate(links, base_url)

            # 현재 URL 제외
            normalized_links.discard(base_url)
            # Also try without trailing slash
            normalized_links.discard(base_url.rstrip("/"))
            normalized_links.discard(base_url + "/")

            # Scope 필터링
            in_scope_links = [
                url
                for url in normalized_links
                if self._scope_checker.is_in_scope(url, context.target)
            ]

            # 자식 Task 생성
            spawned_count = 0
            for url in in_scope_links:
                task_data = {
                    "crawl_url": url,
                    "target_id": context.task.target_id,
                    "project_id": context.task.project_id,
                    "depth": context.depth + 1,
                    "max_depth": context.max_depth,
                    "parent_task_id": context.task.id,
                }
                await self._task_queue.enqueue(task_data)
                spawned_count += 1

            context.set_child_tasks_spawned(spawned_count)
            logger.info(
                "Recurse completed: spawned=%d, total_links=%d, in_scope=%d",
                spawned_count,
                len(links),
                len(in_scope_links),
            )

            return StageResult.ok()

        except Exception as e:
            logger.error("Recurse failed: error=%s", str(e))
            return StageResult.fail(f"Recurse failed: {e}")

    def _normalize_and_deduplicate(self, links: List[str], base_url: str) -> Set[str]:
        """링크 정규화 및 중복 제거.

        Args:
            links: 원시 링크 목록
            base_url: 기본 URL (상대 경로 해석용)

        Returns:
            정규화된 고유 URL 집합
        """
        normalized: Set[str] = set()
        for link in links:
            try:
                # 상대 URL을 절대 URL로 변환
                absolute_url = urljoin(base_url, link)
                normalized.add(absolute_url)
            except Exception:
                continue  # 잘못된 URL은 무시
        return normalized
