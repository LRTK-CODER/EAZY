"""
CrawlManager: 재귀 크롤링 로직 (BFS) 관리

주요 기능:
- 발견된 URL에 대해 자식 Task 생성
- Redis SET으로 방문 URL 중복 제거
- Scope 필터링 적용

Usage:
    from app.services.crawl_manager import CrawlManager

    manager = CrawlManager(session, redis)
    child_tasks = await manager.spawn_child_tasks(
        parent_task_id=1,
        target_id=10,
        project_id=100,
        discovered_urls=["https://example.com/page1"],
        current_depth=0,
        max_depth=3,
        target_url="https://example.com",
        scope=TargetScope.DOMAIN,
    )
"""

import logging
from typing import List, Optional

from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.queue import TaskManager
from app.models.target import TargetScope
from app.models.task import Task, TaskStatus, TaskType
from app.services.scope_filter import ScopeFilter
from app.services.url_normalizer import get_url_hash, normalize_url

logger = logging.getLogger(__name__)


class CrawlManager:
    """재귀 크롤링 관리자"""

    VISITED_KEY_PREFIX = "eazy:crawl:visited"
    VISITED_TTL_SECONDS = 86400  # 24시간

    def __init__(self, session: AsyncSession, redis: Redis):
        """
        CrawlManager 초기화.

        Args:
            session: AsyncSession for database operations
            redis: Redis client for visited URL tracking
        """
        self.session = session
        self.redis = redis
        self.task_manager = TaskManager(redis)

    async def spawn_child_tasks(
        self,
        parent_task_id: int,
        target_id: int,
        project_id: int,
        discovered_urls: List[str],
        current_depth: int,
        max_depth: int,
        target_url: Optional[str] = None,
        scope: Optional[TargetScope] = None,
    ) -> List[Task]:
        """
        발견된 URL에 대해 자식 Task 생성.

        Args:
            parent_task_id: 부모 Task ID
            target_id: Target ID
            project_id: Project ID
            discovered_urls: 크롤링에서 발견된 URL 목록
            current_depth: 현재 크롤링 깊이
            max_depth: 최대 크롤링 깊이
            target_url: Scope 필터링용 타겟 URL
            scope: Scope 설정 (DOMAIN, SUBDOMAIN, URL_ONLY)

        Returns:
            생성된 자식 Task 목록
        """
        # 1. 깊이 제한 확인
        if current_depth >= max_depth:
            logger.debug(f"Max depth reached: {current_depth}/{max_depth}")
            return []

        # 2. 빈 입력 처리
        if not discovered_urls:
            return []

        # 3. URL 정규화 및 배치 내 중복 제거
        # NormalizedUrl is a NewType of str, cast to List[str] for compatibility
        # base_url을 전달하여 상대 URL을 절대 URL로 변환
        normalized_urls: List[str] = list(
            set(
                str(normalize_url(url, base_url=target_url))
                for url in discovered_urls
                if url  # 빈 URL 필터링
            )
        )

        # 4. Scope 필터링
        if target_url and scope:
            scope_filter = ScopeFilter(target_url, scope)
            normalized_urls = scope_filter.filter_urls(normalized_urls)
            logger.debug(f"After scope filter: {len(normalized_urls)} URLs")

        if not normalized_urls:
            return []

        # 5. 방문 URL 필터링 (Redis SET 조회)
        unvisited_urls = await self._filter_unvisited(target_id, normalized_urls)
        logger.debug(f"Unvisited URLs: {len(unvisited_urls)}")

        if not unvisited_urls:
            return []

        # 6. 방문 마킹 (선점 - 다른 워커와의 경쟁 방지)
        await self.mark_visited(target_id, unvisited_urls)

        # 7. 자식 Task 배치 생성
        child_tasks = []
        for url in unvisited_urls:
            task = Task(
                project_id=project_id,
                target_id=target_id,
                type=TaskType.CRAWL,
                status=TaskStatus.PENDING,
                depth=current_depth + 1,
                max_depth=max_depth,
                parent_task_id=parent_task_id,
            )
            self.session.add(task)
            child_tasks.append(task)

        # 8. DB 배치 커밋
        await self.session.commit()
        for task in child_tasks:
            await self.session.refresh(task)

        # 9. Redis 큐에 Enqueue
        for task in child_tasks:
            if task.id is not None:
                await self.task_manager.enqueue_crawl_task(
                    project_id=project_id,
                    target_id=target_id,
                    db_task_id=task.id,
                )

        logger.info(
            f"Spawned {len(child_tasks)} child tasks for parent {parent_task_id}"
        )
        return child_tasks

    async def mark_visited(self, target_id: int, urls: List[str]) -> None:
        """
        Redis SET에 방문 URL 해시 저장.

        Args:
            target_id: Target ID
            urls: 방문한 URL 목록
        """
        if not urls:
            return

        key = f"{self.VISITED_KEY_PREFIX}:{target_id}"

        # Pipeline으로 배치 처리
        pipe = self.redis.pipeline()
        for url in urls:
            url_hash = get_url_hash(url)
            pipe.sadd(key, url_hash)
        pipe.expire(key, self.VISITED_TTL_SECONDS)
        await pipe.execute()

    async def is_visited(self, target_id: int, url: str) -> bool:
        """
        URL이 이미 방문되었는지 확인.

        Args:
            target_id: Target ID
            url: 확인할 URL

        Returns:
            방문 여부
        """
        key = f"{self.VISITED_KEY_PREFIX}:{target_id}"
        url_hash = get_url_hash(url)
        result = await self.redis.sismember(key, url_hash)  # type: ignore[misc]
        return bool(result)

    async def _filter_unvisited(self, target_id: int, urls: List[str]) -> List[str]:
        """
        방문하지 않은 URL만 필터링 (배치).

        Args:
            target_id: Target ID
            urls: 필터링할 URL 목록

        Returns:
            방문하지 않은 URL 목록
        """
        if not urls:
            return []

        key = f"{self.VISITED_KEY_PREFIX}:{target_id}"

        # Pipeline으로 배치 체크
        pipe = self.redis.pipeline()
        for url in urls:
            url_hash = get_url_hash(url)
            pipe.sismember(key, url_hash)

        results = await pipe.execute()

        unvisited = []
        for url, visited in zip(urls, results):
            if not visited:
                unvisited.append(url)

        return unvisited

    async def clear_visited(self, target_id: int) -> None:
        """
        Target의 방문 기록 초기화.

        Args:
            target_id: Target ID
        """
        key = f"{self.VISITED_KEY_PREFIX}:{target_id}"
        await self.redis.delete(key)
