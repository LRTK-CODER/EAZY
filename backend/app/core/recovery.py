"""
Phase 2: 고아 작업 복구 시스템

Worker 크래시로 인해 처리 중 상태로 남은 작업을 감지하고 복구합니다.
- 하트비트 기반 생존 확인
- 타임아웃 초과 작업 자동 복구
- 과도한 복구 시 DLQ 이동
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from redis.asyncio import Redis

from app.core.errors import ErrorCategory
from app.core.dlq import DLQManager
from app.core.utils.json_parser import SafeJsonParser
from app.core.utils import utc_now_tz


logger = logging.getLogger(__name__)


# 상수
ORPHAN_TIMEOUT: int = 600  # 10분 (초)
MAX_RECOVERY_COUNT: int = 3  # 최대 복구 횟수
HEARTBEAT_TTL: int = ORPHAN_TIMEOUT + 60  # 하트비트 TTL (타임아웃 + 여유)


class OrphanRecovery:
    """고아 작업 복구 관리자"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_key = "eazy_task_queue"
        self.processing_key = "eazy_task_queue:processing"
        self.heartbeat_prefix = "eazy:heartbeat:"
        self.dlq_manager = DLQManager(redis)

    async def send_heartbeat(self, task_id: str) -> None:
        """
        작업 처리 중 하트비트를 전송합니다.

        Args:
            task_id: 작업 ID
        """
        key = f"{self.heartbeat_prefix}{task_id}"
        await self.redis.set(key, utc_now_tz().isoformat(), ex=HEARTBEAT_TTL)

    async def clear_heartbeat(self, task_id: str) -> None:
        """
        작업 완료 시 하트비트를 삭제합니다.

        Args:
            task_id: 작업 ID
        """
        key = f"{self.heartbeat_prefix}{task_id}"
        await self.redis.delete(key)

    async def find_orphan_tasks(self) -> List[Dict[str, Any]]:
        """
        고아 작업을 찾습니다.

        고아 작업 조건:
        1. processing 큐에 있음
        2. 하트비트가 없거나 타임아웃 초과

        Returns:
            고아 작업 목록
        """
        orphans = []

        # processing 큐의 모든 작업 조회
        processing_tasks = await self.redis.lrange(self.processing_key, 0, -1)

        for task_json in processing_tasks:
            # Safe JSON parsing
            parse_result = SafeJsonParser.parse(task_json)
            if not parse_result.success:
                # Invalid JSON - treat as orphan with placeholder data
                logger.warning(
                    f"Invalid JSON in processing queue, treating as orphan: "
                    f"{parse_result.error}"
                )
                orphans.append({"_parse_error": parse_result.error, "_raw_json": task_json})
                continue

            task_data = parse_result.data
            task_id = task_data.get("id")

            if not task_id:
                # ID가 없는 작업도 고아로 처리
                orphans.append(task_data)
                continue

            # 하트비트 확인
            heartbeat_key = f"{self.heartbeat_prefix}{task_id}"
            last_heartbeat = await self.redis.get(heartbeat_key)

            if not last_heartbeat:
                # 하트비트 없음 → 고아
                orphans.append(task_data)
                continue

            # 하트비트 타임아웃 확인
            try:
                heartbeat_time = datetime.fromisoformat(last_heartbeat)
                elapsed = (utc_now_tz() - heartbeat_time).total_seconds()

                if elapsed > ORPHAN_TIMEOUT:
                    # 타임아웃 초과 → 고아
                    orphans.append(task_data)
            except (ValueError, TypeError):
                # 잘못된 하트비트 형식 → 고아로 처리
                orphans.append(task_data)

        return orphans

    async def recover_orphan_tasks(self) -> int:
        """
        고아 작업을 복구합니다.

        Returns:
            복구된 작업 수
        """
        orphans = await self.find_orphan_tasks()
        recovered_count = 0

        for task_data in orphans:
            task_id = task_data.get("id", "unknown")
            recovery_count = task_data.get("recovery_count", 0)

            # 원본 task_json 찾기
            processing_tasks = await self.redis.lrange(self.processing_key, 0, -1)
            original_json = None

            for task_json in processing_tasks:
                parse_result = SafeJsonParser.parse(task_json)
                if not parse_result.success:
                    # Invalid JSON - check if it matches raw_json from orphan
                    if task_data.get("_raw_json") == task_json:
                        original_json = task_json
                        break
                    continue
                parsed = parse_result.data
                if parsed.get("id") == task_id:
                    original_json = task_json
                    break

            if not original_json:
                continue

            # processing 큐에서 제거
            await self.redis.lrem(self.processing_key, 1, original_json)

            # 하트비트 삭제
            await self.clear_heartbeat(task_id)

            if recovery_count >= MAX_RECOVERY_COUNT:
                # 최대 복구 횟수 초과 → DLQ로 이동
                await self.dlq_manager.move_to_dlq(
                    task_json=original_json,
                    error=Exception("Max recovery count exceeded"),
                    error_category=ErrorCategory.PERMANENT,
                    retry_count=recovery_count,
                )
            else:
                # 복구: recovery_count 증가 후 원래 큐로
                task_data["recovery_count"] = recovery_count + 1
                task_data["recovered_at"] = utc_now_tz().isoformat()
                updated_json = json.dumps(task_data)
                await self.redis.rpush(self.queue_key, updated_json)

            recovered_count += 1

        return recovered_count

    async def check_and_recover(self) -> int:
        """
        주기적으로 호출하여 고아 작업을 확인하고 복구합니다.

        Returns:
            복구된 작업 수
        """
        return await self.recover_orphan_tasks()
