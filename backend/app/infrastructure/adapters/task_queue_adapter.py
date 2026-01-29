"""TaskQueueAdapter - CrawlManager를 ITaskQueue 포트에 맞게 어댑팅."""

from typing import Any, Dict, List


class TaskQueueAdapter:
    """CrawlManager의 spawn_child_tasks를 ITaskQueue 포트에 맞게 어댑팅.

    RecurseStage에서 사용하기 위한 간단한 enqueue 인터페이스 제공.
    URL들을 배치로 수집한 후 flush()에서 한 번에 spawn_child_tasks 호출.
    """

    def __init__(self, crawl_manager: Any):
        """TaskQueueAdapter 초기화.

        Args:
            crawl_manager: CrawlManager 인스턴스
        """
        self._crawl_manager = crawl_manager
        self._pending_urls: List[str] = []
        self._task_data: Dict[str, Any] = {}

    async def enqueue(self, task_data: Dict[str, Any]) -> None:
        """작업을 큐에 추가 (배치 수집).

        Args:
            task_data: Task 데이터 (crawl_url, target_id, project_id, depth, max_depth, parent_task_id)
        """
        # 첫 번째 task_data에서 메타데이터 저장
        if not self._task_data:
            self._task_data = {
                "parent_task_id": task_data.get("parent_task_id"),
                "target_id": task_data.get("target_id"),
                "project_id": task_data.get("project_id"),
                "depth": task_data.get("depth", 1),
                "max_depth": task_data.get("max_depth", 1),
                "base_url": task_data.get("base_url", ""),
                "scope": task_data.get("scope"),
            }
        self._pending_urls.append(task_data["crawl_url"])

    async def flush(self) -> int:
        """수집된 URL들을 한 번에 spawn_child_tasks로 처리.

        Returns:
            생성된 자식 Task 수
        """
        if not self._pending_urls or not self._task_data:
            return 0

        child_tasks = await self._crawl_manager.spawn_child_tasks(
            parent_task_id=self._task_data["parent_task_id"],
            target_id=self._task_data["target_id"],
            project_id=self._task_data["project_id"],
            discovered_urls=list(self._pending_urls),  # 복사본 전달 (참조 문제 방지)
            current_depth=self._task_data["depth"]
            - 1,  # spawn_child_tasks는 +1 하므로 -1
            max_depth=self._task_data["max_depth"],
            target_url=self._task_data.get("base_url", ""),
            scope=self._task_data.get("scope"),
        )

        count = len(child_tasks) if child_tasks else 0
        self._pending_urls.clear()
        self._task_data.clear()
        return count

    def get_pending_count(self) -> int:
        """대기 중인 URL 수 반환."""
        return len(self._pending_urls)
