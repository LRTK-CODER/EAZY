"""
Phase 2: Redis Queue with BRPOPLPUSH + ACK 패턴
Phase 4.5: Priority Queue Support

작업 손실을 방지하기 위한 안전한 큐 처리:
- dequeue: BRPOPLPUSH로 작업을 processing 큐로 atomic 이동
- ack: 성공 시 processing 큐에서 제거
- nack: 실패 시 원래 큐로 재시도 또는 DLQ로 이동

우선순위 큐 지원 (Phase 4.5):
- 4개 우선순위 레벨: CRITICAL, HIGH, NORMAL, LOW
- 하위호환: priority 미지정 시 NORMAL 사용
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from redis.asyncio import Redis

from app.models.task import TaskType
from app.core.priority import (
    TaskPriority,
    AgingConfig,
    get_queue_key,
    get_next_priority,
    PRIORITY_ORDER,
)


class TaskManager:
    """Redis 기반 작업 큐 관리자"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_key = "eazy_task_queue"
        self.processing_key = "eazy_task_queue:processing"
        self.dlq_key = "eazy_task_queue:dlq"

    async def enqueue_crawl_task(
        self,
        project_id: int,
        target_id: int,
        db_task_id: int,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Enqueue a crawl task into Redis with priority support.

        Args:
            project_id: Project ID
            target_id: Target ID
            db_task_id: Database task ID
            priority: Task priority (default: NORMAL for backward compatibility)

        Returns:
            The unique task ID (UUID) used for tracking in Redis.
        """
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        payload = {
            "id": task_id,
            "db_task_id": db_task_id,
            "type": TaskType.CRAWL.value,
            "project_id": project_id,
            "target_id": target_id,
            "priority": priority.value,
            "timestamp": now.isoformat(),
            "enqueued_at": now.isoformat(),
        }

        # Route to appropriate priority queue
        queue_key = get_queue_key(self.queue_key, priority)
        await self.redis.rpush(queue_key, json.dumps(payload))
        return task_id

    async def dequeue_task(
        self, timeout: int = 5
    ) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        우선순위 순서로 작업을 안전하게 dequeue합니다.

        우선순위 순서: CRITICAL -> HIGH -> NORMAL -> LOW
        각 우선순위 큐를 순차적으로 확인하며, 작업이 있으면 processing 큐로
        atomic하게 이동시킵니다.

        Args:
            timeout: 작업 대기 시간 (초)

        Returns:
            성공 시: (task_data: dict, task_json: str) 튜플
            실패 시: None
        """
        # Try higher priority queues first (non-blocking)
        # CRITICAL, HIGH, NORMAL 순서로 확인
        for priority in PRIORITY_ORDER[:-1]:  # All except LOW
            queue_key = get_queue_key(self.queue_key, priority)

            # Use LMOVE (non-blocking) for priority queues
            # LEFT = take oldest (FIFO), LEFT = push to front of processing
            result = await self.redis.lmove(
                queue_key,
                self.processing_key,
                "LEFT",  # Take from left (oldest first for FIFO)
                "LEFT",
            )

            if result:
                task_json = result
                task_data = json.loads(task_json)
                return task_data, task_json

        # For lowest priority (LOW), use blocking wait with remaining timeout
        lowest_queue = get_queue_key(self.queue_key, PRIORITY_ORDER[-1])
        result = await self.redis.blmove(
            lowest_queue,
            self.processing_key,
            timeout,
            "LEFT",  # Take from left (oldest first for FIFO)
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

        우선순위를 보존하여 원래 우선순위 큐로 반환합니다.
        retry_count를 증가시켜 재시도 횟수를 추적합니다.

        Args:
            task_json: dequeue에서 받은 원본 JSON 문자열
            retry: True면 원래 우선순위 큐로, False면 DLQ로 이동

        Returns:
            bool: 처리 성공 여부
        """
        # processing 큐에서 제거
        await self.redis.lrem(self.processing_key, 1, task_json)

        # Parse task to get priority and update retry_count
        task_data = json.loads(task_json)
        priority_value = task_data.get("priority", TaskPriority.NORMAL.value)
        priority = TaskPriority(priority_value)

        if retry:
            # Increment retry_count
            task_data["retry_count"] = task_data.get("retry_count", 0) + 1
            updated_json = json.dumps(task_data)

            # Return to the same priority queue (front for priority retry)
            queue_key = get_queue_key(self.queue_key, priority)
            await self.redis.lpush(queue_key, updated_json)
        else:
            # DLQ로 이동 (priority info preserved in payload)
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

    async def get_all_queue_lengths(self) -> Dict[str, int]:
        """
        모든 우선순위 큐와 시스템 큐의 길이를 반환합니다.

        Returns:
            Dict with keys: critical, high, normal, low, processing, dlq
        """
        return {
            "critical": await self.redis.llen(
                get_queue_key(self.queue_key, TaskPriority.CRITICAL)
            ),
            "high": await self.redis.llen(
                get_queue_key(self.queue_key, TaskPriority.HIGH)
            ),
            "normal": await self.redis.llen(
                get_queue_key(self.queue_key, TaskPriority.NORMAL)
            ),
            "low": await self.redis.llen(
                get_queue_key(self.queue_key, TaskPriority.LOW)
            ),
            "processing": await self.redis.llen(self.processing_key),
            "dlq": await self.redis.llen(self.dlq_key),
        }

    async def promote_aged_tasks(self, config: AgingConfig = None) -> int:
        """
        Promote tasks that have been waiting too long in lower priority queues.

        This prevents starvation of low priority tasks by promoting them
        to higher priority queues after a configured threshold.

        Args:
            config: Aging configuration (default: AgingConfig())

        Returns:
            Number of tasks promoted
        """
        if config is None:
            config = AgingConfig()

        promoted_count = 0
        now = datetime.now(timezone.utc)

        # Define promotion thresholds for each priority level
        promotion_thresholds = {
            TaskPriority.LOW: config.low_to_normal_seconds,
            TaskPriority.NORMAL: config.normal_to_high_seconds,
            TaskPriority.HIGH: config.high_to_critical_seconds,
        }

        # Process queues that can be promoted (LOW, NORMAL, HIGH - not CRITICAL)
        for priority in [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH]:
            queue_key = get_queue_key(self.queue_key, priority)
            threshold_seconds = promotion_thresholds[priority]
            next_priority = get_next_priority(priority)

            if next_priority is None:
                continue

            next_queue_key = get_queue_key(self.queue_key, next_priority)

            # Get all tasks from the queue
            tasks_json = await self.redis.lrange(queue_key, 0, -1)

            for task_json in tasks_json:
                try:
                    task_data = json.loads(task_json)
                    enqueued_at_str = task_data.get("enqueued_at")

                    if not enqueued_at_str:
                        continue

                    enqueued_at = datetime.fromisoformat(enqueued_at_str)
                    age_seconds = (now - enqueued_at).total_seconds()

                    if age_seconds >= threshold_seconds:
                        # Remove from current queue
                        removed = await self.redis.lrem(queue_key, 1, task_json)

                        if removed > 0:
                            # Update priority in payload
                            original_priority = task_data.get(
                                "original_priority", task_data.get("priority")
                            )
                            task_data["original_priority"] = original_priority
                            task_data["priority"] = next_priority.value
                            # Reset enqueued_at to prevent cascading promotions
                            # in the same call - task starts fresh at new priority
                            task_data["enqueued_at"] = now.isoformat()

                            # Add to next priority queue
                            await self.redis.rpush(
                                next_queue_key, json.dumps(task_data)
                            )
                            promoted_count += 1
                except (json.JSONDecodeError, ValueError):
                    continue

        return promoted_count
