"""Task queue port interface."""

from typing import Any, Dict, Optional, Protocol, Tuple

from app.core.priority import TaskPriority


class ITaskQueue(Protocol):
    """Task 큐 인터페이스 - 기존 TaskPriority 사용"""

    async def enqueue(self, task_data: Dict[str, Any], priority: TaskPriority) -> str:
        """작업을 큐에 추가."""
        ...

    async def dequeue(self, timeout: float) -> Optional[Tuple[Dict[str, Any], str]]:
        """작업을 큐에서 가져옴."""
        ...

    async def ack(self, task_json: str) -> bool:
        """작업 완료 확인."""
        ...

    async def nack(self, task_json: str, error: str, retry: bool) -> bool:
        """작업 실패 처리."""
        ...
