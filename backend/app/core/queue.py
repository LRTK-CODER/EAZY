"""
Phase 2: Redis Queue with BRPOPLPUSH + ACK 패턴

작업 손실을 방지하기 위한 안전한 큐 처리:
- dequeue: BRPOPLPUSH로 작업을 processing 큐로 atomic 이동
- ack: 성공 시 processing 큐에서 제거
- nack: 실패 시 원래 큐로 재시도 또는 DLQ로 이동
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from redis.asyncio import Redis

from app.models.task import TaskType


class TaskManager:
    """Redis 기반 작업 큐 관리자"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_key = "eazy_task_queue"
        self.processing_key = "eazy_task_queue:processing"
        self.dlq_key = "eazy_task_queue:dlq"

    async def enqueue_crawl_task(
        self, project_id: int, target_id: int, db_task_id: int
    ) -> str:
        """
        Enqueue a crawl task into Redis.
        Returns the unique task ID (UUID) used for tracking in Redis.
        """
        task_id = str(uuid.uuid4())
        payload = {
            "id": task_id,
            "db_task_id": db_task_id,
            "type": TaskType.CRAWL.value,
            "project_id": project_id,
            "target_id": target_id,
            "timestamp": str(datetime.now()),
        }
        await self.redis.rpush(self.queue_key, json.dumps(payload))
        return task_id

    async def dequeue_task(
        self, timeout: int = 5
    ) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        BRPOPLPUSH를 사용하여 작업을 안전하게 dequeue합니다.

        작업을 원래 큐에서 processing 큐로 atomic하게 이동시킵니다.
        Worker가 크래시해도 작업이 processing 큐에 남아있어 복구 가능합니다.

        Args:
            timeout: 작업 대기 시간 (초)

        Returns:
            성공 시: (task_data: dict, task_json: str) 튜플
            실패 시: None
        """
        # BRPOPLPUSH: 원래 큐 → processing 큐로 atomic 이동
        # redis-py에서는 brpoplpush가 deprecated되어 blmove 사용
        result = await self.redis.blmove(
            self.queue_key,
            self.processing_key,
            timeout,
            "RIGHT",
            "LEFT",
        )

        if result:
            task_json = result
            task_data = json.loads(task_json)
            return task_data, task_json

        return None

    async def ack_task(self, task_json: str) -> bool:
        """
        작업 완료를 확인하고 processing 큐에서 제거합니다.

        Args:
            task_json: dequeue에서 받은 원본 JSON 문자열

        Returns:
            bool: 제거 성공 여부
        """
        removed = await self.redis.lrem(self.processing_key, 1, task_json)
        return removed > 0

    async def nack_task(self, task_json: str, retry: bool = True) -> bool:
        """
        작업 실패를 처리합니다.

        Args:
            task_json: dequeue에서 받은 원본 JSON 문자열
            retry: True면 원래 큐로, False면 DLQ로 이동

        Returns:
            bool: 처리 성공 여부
        """
        # processing 큐에서 제거
        await self.redis.lrem(self.processing_key, 1, task_json)

        if retry:
            # 원래 큐의 앞쪽에 추가 (우선 재시도)
            await self.redis.lpush(self.queue_key, task_json)
        else:
            # DLQ로 이동
            await self.redis.lpush(self.dlq_key, task_json)

        return True

    async def get_processing_tasks(self) -> List[Dict[str, Any]]:
        """
        현재 processing 중인 작업 목록을 조회합니다.

        Returns:
            List[Dict]: processing 큐의 모든 작업
        """
        tasks_json = await self.redis.lrange(self.processing_key, 0, -1)
        return [json.loads(t) for t in tasks_json]

    async def get_dlq_tasks(self) -> List[Dict[str, Any]]:
        """
        DLQ의 작업 목록을 조회합니다.

        Returns:
            List[Dict]: DLQ의 모든 작업
        """
        tasks_json = await self.redis.lrange(self.dlq_key, 0, -1)
        return [json.loads(t) for t in tasks_json]

    async def get_queue_length(self) -> int:
        """원래 큐의 길이를 반환합니다."""
        return await self.redis.llen(self.queue_key)

    async def get_processing_length(self) -> int:
        """processing 큐의 길이를 반환합니다."""
        return await self.redis.llen(self.processing_key)

    async def get_dlq_length(self) -> int:
        """DLQ의 길이를 반환합니다."""
        return await self.redis.llen(self.dlq_key)
