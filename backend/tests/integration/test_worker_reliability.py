"""
Phase 2 Day 5: Worker 안정성 통합 테스트

Worker의 ACK/NACK 패턴, 에러 처리, 재시도 로직을 검증합니다.
"""

import json
from unittest.mock import patch

import pytest
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import ErrorCategory
from app.core.queue import TaskManager
from app.models.task import TaskStatus


@pytest.fixture
async def redis_client() -> Redis:
    """테스트용 Redis 클라이언트"""
    from app.core.config import settings

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_all_queues(redis_client: Redis):
    """테스트 전후 모든 큐 정리"""
    keys_to_clean = [
        "eazy_task_queue",
        "eazy_task_queue:processing",
        "eazy_task_queue:dlq",
    ]

    for key in keys_to_clean:
        await redis_client.delete(key)

    # 하트비트와 메타데이터 정리
    for pattern in ["eazy:heartbeat:*", "eazy:dlq:meta:*"]:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)

    yield

    for key in keys_to_clean:
        await redis_client.delete(key)

    for pattern in ["eazy:heartbeat:*", "eazy:dlq:meta:*"]:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)


class TestWorkerAckOnSuccess:
    """성공 시 ACK 테스트"""

    @pytest.mark.asyncio
    async def test_worker_acks_on_success(
        self, db_session: AsyncSession, redis_client: Redis, clean_all_queues
    ):
        """작업 성공 시 processing 큐에서 제거되어야 함"""
        from app.models.project import Project
        from app.models.target import Target, TargetScope
        from app.models.task import Task, TaskType
        from app.worker import process_one_task

        # Given: 프로젝트, 타겟, 태스크 생성
        project = Project(name="ACK Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="ACK Target",
            project_id=project.id,
            url="http://example.com",
            scope=TargetScope.DOMAIN,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # 작업 enqueue
        tm = TaskManager(redis_client)
        await tm.enqueue_crawl_task(project.id, target.id, db_task_id=task.id)

        # When: Worker 실행 (성공)
        with patch("app.services.crawler_service.CrawlerService.crawl") as mock_crawl:
            mock_crawl.return_value = (["http://example.com/page1"], {})
            await process_one_task(db_session, tm)

        # Then: processing 큐가 비어있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

        # Task 상태가 COMPLETED여야 함
        await db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED


class TestWorkerNackOnError:
    """에러 시 NACK 테스트"""

    @pytest.mark.asyncio
    async def test_worker_handles_retryable_error(
        self, db_session: AsyncSession, redis_client: Redis, clean_all_queues
    ):
        """재시도 가능한 에러 발생 시 적절히 처리되어야 함"""
        from app.models.project import Project
        from app.models.target import Target, TargetScope
        from app.models.task import Task, TaskType
        from app.worker import process_one_task

        # Given: 프로젝트, 타겟, 태스크 생성
        project = Project(name="Retry Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Retry Target",
            project_id=project.id,
            url="http://timeout-example.com",
            scope=TargetScope.DOMAIN,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        tm = TaskManager(redis_client)
        await tm.enqueue_crawl_task(project.id, target.id, db_task_id=task.id)

        # When: Worker 실행 (타임아웃 에러)
        with patch("app.services.crawler_service.CrawlerService.crawl") as mock_crawl:
            mock_crawl.side_effect = TimeoutError("Connection timed out")

            try:
                await process_one_task(db_session, tm)
            except TimeoutError:
                pass  # 에러는 예상됨

        # Then: Task 상태가 FAILED여야 함
        await db_session.refresh(task)
        assert task.status == TaskStatus.FAILED


class TestErrorClassificationIntegration:
    """에러 분류 통합 테스트"""

    @pytest.mark.asyncio
    async def test_classify_error_in_context(self, redis_client: Redis):
        """에러 분류가 올바르게 동작하는지 확인"""
        from app.core.errors import classify_error

        # 다양한 에러 타입 테스트
        test_cases = [
            (TimeoutError("timeout"), ErrorCategory.RETRYABLE),
            (ConnectionError("refused"), ErrorCategory.RETRYABLE),
            (ValueError("invalid"), ErrorCategory.PERMANENT),
            (Exception("404 not found"), ErrorCategory.PERMANENT),
            (Exception("rate limit exceeded"), ErrorCategory.TRANSIENT),
            (Exception("503 service unavailable"), ErrorCategory.TRANSIENT),
        ]

        for error, expected_category in test_cases:
            result = classify_error(error)
            assert result == expected_category, f"Failed for {error}"


class TestDLQIntegration:
    """DLQ 통합 테스트"""

    @pytest.mark.asyncio
    async def test_permanent_error_goes_to_dlq(
        self, redis_client: Redis, clean_all_queues
    ):
        """영구적 에러는 DLQ로 이동해야 함"""
        from app.core.dlq import DLQManager

        dlq_manager = DLQManager(redis_client)

        # Given: 작업 생성
        task_data = {"id": "perm-error-1", "db_task_id": 100}
        task_json = json.dumps(task_data)

        # When: DLQ로 이동
        await dlq_manager.move_to_dlq(
            task_json=task_json,
            error=ValueError("Invalid URL format"),
            error_category=ErrorCategory.PERMANENT,
            retry_count=0,
        )

        # Then: DLQ에 존재
        dlq_tasks = await dlq_manager.list_dlq_tasks()
        assert len(dlq_tasks) == 1
        assert dlq_tasks[0]["task_data"]["id"] == "perm-error-1"
        assert dlq_tasks[0]["meta"]["error_category"] == "permanent"


class TestRecoveryIntegration:
    """복구 통합 테스트"""

    @pytest.mark.asyncio
    async def test_orphan_recovery_flow(self, redis_client: Redis, clean_all_queues):
        """고아 작업 복구 전체 흐름 테스트"""
        from app.core.queue import TaskManager
        from app.core.recovery import OrphanRecovery

        tm = TaskManager(redis_client)
        recovery = OrphanRecovery(redis_client)

        # Given: 작업을 enqueue하고 dequeue (processing으로 이동)
        await tm.enqueue_crawl_task(project_id=1, target_id=1, db_task_id=100)
        result = await tm.dequeue_task(timeout=1)
        assert result is not None

        # processing 큐에 작업이 있음
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 1

        # When: 고아 복구 실행 (하트비트 없으므로 고아로 감지됨)
        recovered = await recovery.recover_orphan_tasks()

        # Then: 원래 큐로 복구됨
        assert recovered == 1

        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 1

        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0
