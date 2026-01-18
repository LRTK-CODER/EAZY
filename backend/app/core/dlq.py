"""
Phase 2: Dead Letter Queue (DLQ) 관리자

실패한 작업을 관리하고 분석할 수 있는 DLQ 시스템:
- 실패 작업과 메타데이터 저장
- 목록 조회 및 분석
- 수동 재시도
- 영구 삭제
"""

import json
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis

from app.core.errors import ErrorCategory
from app.core.utils import utc_now_tz


class DLQManager:
    """Dead Letter Queue 관리자"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_key = "eazy_task_queue"
        self.dlq_key = "eazy_task_queue:dlq"
        self.meta_prefix = "eazy:dlq:meta:"

    async def move_to_dlq(
        self,
        task_json: str,
        error: Exception,
        error_category: ErrorCategory,
        retry_count: int,
    ) -> None:
        """
        실패한 작업을 DLQ로 이동하고 메타데이터를 저장합니다.

        Args:
            task_json: 원본 작업 JSON 문자열
            error: 발생한 예외
            error_category: 에러 분류
            retry_count: 재시도 횟수
        """
        task_data = json.loads(task_json)
        task_id = task_data.get("id", "unknown")

        # 메타데이터 저장
        meta = {
            "original_task": task_json,
            "error_message": str(error),
            "error_category": error_category.value,
            "retry_count": str(retry_count),
            "failed_at": utc_now_tz().isoformat(),
        }

        meta_key = f"{self.meta_prefix}{task_id}"
        await self.redis.hset(meta_key, mapping=meta)

        # DLQ 리스트에 task_id 추가
        await self.redis.lpush(self.dlq_key, task_id)

    async def list_dlq_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        DLQ의 작업 목록을 메타데이터와 함께 조회합니다.

        Args:
            limit: 최대 조회 개수

        Returns:
            작업 데이터와 메타데이터가 포함된 딕셔너리 리스트
        """
        # DLQ에서 task_id 목록 조회
        task_ids = await self.redis.lrange(self.dlq_key, 0, limit - 1)

        results = []
        for task_id in task_ids:
            meta_key = f"{self.meta_prefix}{task_id}"
            meta = await self.redis.hgetall(meta_key)

            if meta:
                original_task = json.loads(meta.get("original_task", "{}"))
                results.append(
                    {
                        "task_id": task_id,
                        "task_data": original_task,
                        "meta": {
                            "error_message": meta.get("error_message"),
                            "error_category": meta.get("error_category"),
                            "retry_count": int(meta.get("retry_count", 0)),
                            "failed_at": meta.get("failed_at"),
                        },
                    }
                )

        return results

    async def retry_dlq_task(self, task_id: str) -> bool:
        """
        DLQ 작업을 원래 큐로 다시 이동하여 재시도합니다.

        Args:
            task_id: 재시도할 작업 ID

        Returns:
            성공 여부
        """
        meta_key = f"{self.meta_prefix}{task_id}"
        meta = await self.redis.hgetall(meta_key)

        if not meta:
            return False

        original_task = meta.get("original_task")
        if not original_task:
            return False

        # 원래 큐에 추가
        await self.redis.lpush(self.queue_key, original_task)

        # DLQ에서 제거
        await self.redis.lrem(self.dlq_key, 1, task_id)

        # 메타데이터 삭제
        await self.redis.delete(meta_key)

        return True

    async def purge_dlq_task(self, task_id: str) -> bool:
        """
        DLQ 작업을 완전히 삭제합니다 (재시도 없이).

        Args:
            task_id: 삭제할 작업 ID

        Returns:
            성공 여부
        """
        meta_key = f"{self.meta_prefix}{task_id}"

        # DLQ에서 제거
        await self.redis.lrem(self.dlq_key, 1, task_id)

        # 메타데이터 삭제
        await self.redis.delete(meta_key)

        return True

    async def get_dlq_length(self) -> int:
        """DLQ의 작업 개수를 반환합니다."""
        return await self.redis.llen(self.dlq_key)

    async def get_task_meta(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 작업의 메타데이터를 조회합니다."""
        meta_key = f"{self.meta_prefix}{task_id}"
        meta = await self.redis.hgetall(meta_key)

        if not meta:
            return None

        return {
            "original_task": json.loads(meta.get("original_task", "{}")),
            "error_message": meta.get("error_message"),
            "error_category": meta.get("error_category"),
            "retry_count": int(meta.get("retry_count", 0)),
            "failed_at": meta.get("failed_at"),
        }
