"""
Phase 2 Day 3: DLQ 관리자 테스트

TDD RED 단계 - dlq.py 구현 전에 실패해야 함
"""

import json

import pytest
from redis.asyncio import Redis

from app.core.errors import ErrorCategory


@pytest.fixture
async def redis_client() -> Redis:
    """테스트용 Redis 클라이언트"""
    from app.core.config import settings

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_dlq(redis_client: Redis):
    """테스트 전후 DLQ 관련 키 정리"""
    # 테스트 전 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")

    # DLQ 메타데이터 키 패턴 정리
    keys = await redis_client.keys("eazy:dlq:meta:*")
    if keys:
        await redis_client.delete(*keys)

    yield

    # 테스트 후 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")

    keys = await redis_client.keys("eazy:dlq:meta:*")
    if keys:
        await redis_client.delete(*keys)


class TestMoveToOrq:
    """move_to_dlq() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_move_to_dlq_stores_metadata(self, redis_client: Redis, clean_dlq):
        """DLQ 이동 시 메타데이터가 저장되어야 함"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {
            "id": "task-123",
            "db_task_id": 100,
            "type": "crawl",
            "target_id": 1,
        }
        task_json = json.dumps(task_data)
        error = Exception("Connection timeout")

        # When: DLQ로 이동
        await dlq_manager.move_to_dlq(
            task_json=task_json,
            error=error,
            error_category=ErrorCategory.RETRYABLE,
            retry_count=3,
        )

        # Then: 메타데이터가 저장되어야 함
        meta = await redis_client.hgetall("eazy:dlq:meta:task-123")
        assert meta is not None
        assert meta["error_message"] == "Connection timeout"
        assert meta["error_category"] == "retryable"
        assert meta["retry_count"] == "3"
        assert "failed_at" in meta

    @pytest.mark.asyncio
    async def test_move_to_dlq_adds_to_list(self, redis_client: Redis, clean_dlq):
        """DLQ 이동 시 DLQ 리스트에 추가되어야 함"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {"id": "task-456", "db_task_id": 200}
        task_json = json.dumps(task_data)

        await dlq_manager.move_to_dlq(
            task_json=task_json,
            error=Exception("Permanent failure"),
            error_category=ErrorCategory.PERMANENT,
            retry_count=0,
        )

        # Then: DLQ 리스트에 추가되어야 함
        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 1

    @pytest.mark.asyncio
    async def test_dlq_preserves_original_task_data(
        self, redis_client: Redis, clean_dlq
    ):
        """DLQ에 원본 작업 데이터가 보존되어야 함"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {
            "id": "task-789",
            "db_task_id": 300,
            "type": "crawl",
            "project_id": 1,
            "target_id": 5,
        }
        task_json = json.dumps(task_data)

        await dlq_manager.move_to_dlq(
            task_json=task_json,
            error=Exception("Error"),
            error_category=ErrorCategory.PERMANENT,
            retry_count=1,
        )

        # Then: 메타데이터에 원본 작업 데이터가 저장되어야 함
        meta = await redis_client.hgetall("eazy:dlq:meta:task-789")
        original_task = json.loads(meta["original_task"])
        assert original_task["db_task_id"] == 300
        assert original_task["target_id"] == 5


class TestListDlqTasks:
    """list_dlq_tasks() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_list_dlq_tasks_returns_with_meta(
        self, redis_client: Redis, clean_dlq
    ):
        """DLQ 작업 목록과 메타데이터를 함께 조회"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        # Given: 여러 작업을 DLQ에 추가
        for i in range(3):
            task_data = {"id": f"task-{i}", "db_task_id": i * 100}
            await dlq_manager.move_to_dlq(
                task_json=json.dumps(task_data),
                error=Exception(f"Error {i}"),
                error_category=ErrorCategory.PERMANENT,
                retry_count=i,
            )

        # When: DLQ 목록 조회
        tasks = await dlq_manager.list_dlq_tasks()

        # Then: 3개 작업과 메타데이터
        assert len(tasks) == 3
        for task in tasks:
            assert "task_data" in task
            assert "meta" in task
            assert "error_message" in task["meta"]

    @pytest.mark.asyncio
    async def test_list_dlq_tasks_with_limit(self, redis_client: Redis, clean_dlq):
        """limit 파라미터로 조회 개수 제한"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        # Given: 5개 작업 추가
        for i in range(5):
            task_data = {"id": f"task-{i}", "db_task_id": i}
            await dlq_manager.move_to_dlq(
                task_json=json.dumps(task_data),
                error=Exception("Error"),
                error_category=ErrorCategory.PERMANENT,
                retry_count=0,
            )

        # When: limit=2로 조회
        tasks = await dlq_manager.list_dlq_tasks(limit=2)

        # Then: 2개만 반환
        assert len(tasks) == 2


class TestRetryDlqTask:
    """retry_dlq_task() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_retry_dlq_moves_back_to_queue(self, redis_client: Redis, clean_dlq):
        """DLQ 작업을 원래 큐로 다시 이동"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {"id": "task-retry-1", "db_task_id": 100}
        task_json = json.dumps(task_data)

        await dlq_manager.move_to_dlq(
            task_json=task_json,
            error=Exception("Temporary error"),
            error_category=ErrorCategory.RETRYABLE,
            retry_count=2,
        )

        # When: 재시도
        success = await dlq_manager.retry_dlq_task("task-retry-1")

        # Then: 원래 큐에 추가
        assert success is True
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 1

        # DLQ에서 제거
        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 0

    @pytest.mark.asyncio
    async def test_retry_dlq_clears_metadata(self, redis_client: Redis, clean_dlq):
        """재시도 시 DLQ 메타데이터가 삭제되어야 함"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {"id": "task-retry-2", "db_task_id": 200}
        await dlq_manager.move_to_dlq(
            task_json=json.dumps(task_data),
            error=Exception("Error"),
            error_category=ErrorCategory.RETRYABLE,
            retry_count=1,
        )

        # When: 재시도
        await dlq_manager.retry_dlq_task("task-retry-2")

        # Then: 메타데이터 삭제
        meta = await redis_client.hgetall("eazy:dlq:meta:task-retry-2")
        assert meta == {}

    @pytest.mark.asyncio
    async def test_retry_nonexistent_task_returns_false(
        self, redis_client: Redis, clean_dlq
    ):
        """존재하지 않는 작업 재시도 시 False 반환"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        success = await dlq_manager.retry_dlq_task("nonexistent-task")
        assert success is False


class TestPurgeDlqTask:
    """purge_dlq_task() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_purge_dlq_removes_completely(self, redis_client: Redis, clean_dlq):
        """DLQ 작업 완전 삭제"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        task_data = {"id": "task-purge-1", "db_task_id": 100}
        await dlq_manager.move_to_dlq(
            task_json=json.dumps(task_data),
            error=Exception("Fatal error"),
            error_category=ErrorCategory.PERMANENT,
            retry_count=3,
        )

        # When: 삭제
        success = await dlq_manager.purge_dlq_task("task-purge-1")

        # Then: DLQ와 메타데이터 모두 삭제
        assert success is True

        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 0

        meta = await redis_client.hgetall("eazy:dlq:meta:task-purge-1")
        assert meta == {}

        # 원래 큐에도 추가되지 않음
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 0
