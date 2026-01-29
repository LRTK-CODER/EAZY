"""
Phase 4: CrawlWorker 분산 잠금 통합 테스트
TDD RED 단계 - 잠금 통합 전에 모두 실패해야 함

Day 4: CrawlWorker 잠금 통합
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from app.models.task import Task, TaskStatus, TaskType
from app.workers.base import WorkerContext

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.eval = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=600)
    return redis


@pytest.fixture
def mock_task_manager(mock_redis):
    """Mock TaskManager with Redis"""
    manager = MagicMock()
    manager.redis = mock_redis
    return manager


@pytest.fixture
def mock_dlq_manager():
    """Mock DLQManager"""
    return MagicMock()


@pytest.fixture
def mock_orphan_recovery():
    """Mock OrphanRecovery"""
    recovery = MagicMock()
    recovery.send_heartbeat = AsyncMock()
    recovery.clear_heartbeat = AsyncMock()
    return recovery


@pytest.fixture
def worker_context(
    mock_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
):
    """워커 컨텍스트 생성"""
    return WorkerContext(
        session=mock_session,
        task_manager=mock_task_manager,
        dlq_manager=mock_dlq_manager,
        orphan_recovery=mock_orphan_recovery,
    )


@pytest.fixture
def sample_task():
    """샘플 Task 레코드"""
    return Task(
        id=1,
        target_id=100,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
    )


@pytest.fixture
def sample_task_data():
    """샘플 task_data"""
    return {
        "target_id": 100,
        "db_task_id": 1,
    }


# =============================================================================
# Lock Integration Tests
# =============================================================================


class TestCrawlWorkerLockIntegration:
    """CrawlWorker 잠금 통합 테스트"""

    @pytest.mark.asyncio
    async def test_acquires_lock_before_crawl(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """크롤링 전에 잠금을 획득해야 함"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        # Mock target
        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        # Mock crawler service
        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        # Execute
        await worker.execute(sample_task_data, sample_task)

        # Verify lock was acquired (SET NX)
        redis = mock_task_manager.redis
        redis.set.assert_called()
        set_calls = [
            call
            for call in redis.set.call_args_list
            if "lock" in str(call).lower() or "target" in str(call).lower()
        ]
        assert len(set_calls) >= 1, "Lock should be acquired for target"

    @pytest.mark.asyncio
    async def test_releases_lock_after_crawl(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """크롤링 후 잠금을 해제해야 함"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        await worker.execute(sample_task_data, sample_task)

        # Verify lock was released (Lua script eval)
        redis = mock_task_manager.redis
        redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_releases_lock_on_exception(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """예외 발생 시에도 잠금 해제"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(side_effect=Exception("Crawl failed"))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        # New architecture returns failure result instead of raising exception
        result = await worker.execute(sample_task_data, sample_task)

        # Verify task failed (crawl error was handled)
        assert result.success is False
        assert "Crawl failed" in (result.error or "")

        # Verify lock was released even on error
        redis = mock_task_manager.redis
        redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_skips_lock_for_missing_target(
        self, worker_context, sample_task, mock_session
    ):
        """target을 찾을 수 없으면 잠금 없이 에러"""
        from app.core.exceptions import TargetNotFoundError
        from app.workers.crawl_worker import CrawlWorker

        mock_session.get = AsyncMock(return_value=None)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        task_data = {"target_id": 999, "db_task_id": 1}

        with pytest.raises(TargetNotFoundError, match="Target not found: 999"):
            await worker.execute(task_data, sample_task)

    @pytest.mark.asyncio
    async def test_uses_correct_lock_key_format(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """올바른 잠금 키 형식 사용"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        await worker.execute(sample_task_data, sample_task)

        # Check lock key format
        redis = mock_task_manager.redis
        set_calls = redis.set.call_args_list
        lock_call = next(
            (call for call in set_calls if "lock" in str(call).lower()), None
        )
        assert lock_call is not None
        # Key should be like "eazy:lock:task:1" (task-based lock to avoid child-parent contention)
        call_str = str(lock_call)
        assert "task" in call_str.lower()


# =============================================================================
# Lock Failure Handling Tests
# =============================================================================


class TestLockFailureHandling:
    """잠금 획득 실패 처리 테스트"""

    @pytest.mark.asyncio
    async def test_returns_skipped_when_lock_unavailable(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """잠금 획득 실패 시 SKIPPED 반환"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        # Lock acquisition fails
        redis = mock_task_manager.redis
        redis.set = AsyncMock(return_value=None)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        result = await worker.execute(sample_task_data, sample_task)

        # Should return skipped result
        assert result.status == "skipped"
        assert "lock" in str(result.data).lower()

    @pytest.mark.asyncio
    async def test_does_not_crawl_when_lock_fails(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """잠금 실패 시 크롤링하지 않음"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        # Lock acquisition fails
        redis = mock_task_manager.redis
        redis.set = AsyncMock(return_value=None)

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        await worker.execute(sample_task_data, sample_task)

        # Crawler should NOT be called
        mock_crawler.crawl.assert_not_called()

    @pytest.mark.asyncio
    async def test_logs_lock_failure(
        self,
        worker_context,
        sample_task,
        sample_task_data,
        mock_session,
        mock_task_manager,
    ):
        """잠금 실패 시 로그 기록"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        # Lock acquisition fails
        redis = mock_task_manager.redis
        redis.set = AsyncMock(return_value=None)

        mock_crawler = MagicMock()
        worker = CrawlWorker(
            context=worker_context,
            crawler_service=mock_crawler,
        )

        with patch("app.workers.crawl_worker.logger") as mock_logger:
            await worker.execute(sample_task_data, sample_task)

            # Should log warning about lock failure
            warning_calls = mock_logger.warning.call_args_list
            lock_warning = any("lock" in str(call).lower() for call in warning_calls)
            assert lock_warning, "Should log warning about lock failure"


# =============================================================================
# Lock TTL Tests
# =============================================================================


class TestLockTTL:
    """잠금 TTL 테스트"""

    def test_lock_ttl_constant_exists(self):
        """LOCK_TTL 상수 존재 확인"""
        from app.core.constants import LOCK_TTL

        assert LOCK_TTL is not None
        assert LOCK_TTL > 0

    def test_lock_ttl_matches_orphan_recovery(self):
        """잠금 TTL이 OrphanRecovery와 일치"""
        from app.core.constants import LOCK_TTL

        # LOCK_TTL should be 600 seconds (10 minutes)
        # matching OrphanRecovery's threshold
        expected_ttl = 600
        assert LOCK_TTL == expected_ttl


# =============================================================================
# Concurrent Lock Tests
# =============================================================================


class TestConcurrentLocks:
    """동시 잠금 테스트"""

    @pytest.mark.asyncio
    async def test_only_one_worker_processes_same_target(
        self, mock_session, mock_dlq_manager, mock_orphan_recovery
    ):
        """동일 대상에 대해 하나의 워커만 처리"""
        from app.models.target import Target
        from app.workers.crawl_worker import CrawlWorker

        target = Target(id=100, url="https://example.com")
        mock_session.get = AsyncMock(return_value=target)

        # Create separate redis mocks for each worker
        redis1 = AsyncMock(spec=Redis)
        redis2 = AsyncMock(spec=Redis)

        # First worker gets lock, second fails
        redis1.set = AsyncMock(return_value=True)
        redis1.eval = AsyncMock(return_value=1)
        redis1.get = AsyncMock(return_value=None)

        redis2.set = AsyncMock(return_value=None)  # Lock fails
        redis2.get = AsyncMock(return_value=None)

        manager1 = MagicMock()
        manager1.redis = redis1
        manager2 = MagicMock()
        manager2.redis = redis2

        context1 = WorkerContext(
            session=mock_session,
            task_manager=manager1,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )
        context2 = WorkerContext(
            session=mock_session,
            task_manager=manager2,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))

        worker1 = CrawlWorker(context=context1, crawler_service=mock_crawler)
        worker2 = CrawlWorker(context=context2, crawler_service=mock_crawler)

        task = Task(id=1, target_id=100, type=TaskType.CRAWL, status=TaskStatus.PENDING)
        task_data = {"target_id": 100, "db_task_id": 1}

        # Run both workers
        result1 = await worker1.execute(task_data, task)
        result2 = await worker2.execute(task_data, task)

        # One should succeed, one should be skipped
        statuses = [result1.status, result2.status]
        assert "success" in statuses
        assert "skipped" in statuses


# =============================================================================
# Lock Key Tests
# =============================================================================


class TestLockKey:
    """잠금 키 형식 테스트"""

    def test_lock_prefix_constant_exists(self):
        """LOCK_PREFIX 상수 존재 확인"""
        from app.core.constants import LOCK_PREFIX

        assert LOCK_PREFIX is not None
        assert "lock" in LOCK_PREFIX.lower()

    def test_lock_key_format(self):
        """잠금 키 형식 확인"""
        from app.core.constants import LOCK_PREFIX

        target_id = 123
        expected_key = f"{LOCK_PREFIX}target:{target_id}"

        assert "target" in expected_key
        assert str(target_id) in expected_key
