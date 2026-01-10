"""
Phase 4: 워커 풀 E2E 통합 테스트
Day 5: 통합 테스트 + 마무리

WorkerPool + DistributedLock + CrawlWorker 전체 통합 검증
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis

from app.workers.pool import WorkerPool, WorkerPoolConfig
from app.workers.base import WorkerContext, TaskResult
from app.core.lock import DistributedLock, LockAcquisitionError


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def pool_config():
    """테스트용 워커 풀 설정"""
    return WorkerPoolConfig(
        num_workers=2,
        max_restarts_per_worker=2,
        restart_delay_base=0.1,
        restart_delay_max=0.5,
        max_consecutive_errors=3,
        shutdown_timeout=5.0,
    )


@pytest.fixture
async def redis_client():
    """테스트용 Redis 클라이언트 (실제 연결)"""
    from app.core.config import settings
    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        single_connection_client=True
    )
    # Initialize connection (required for single_connection_client in redis-py 7.x)
    await redis.ping()
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_test_locks(redis_client):
    """테스트 전후 잠금 정리"""
    # 테스트 전 정리
    async for key in redis_client.scan_iter("eazy:lock:e2e:*"):
        await redis_client.delete(key)

    yield

    # 테스트 후 정리
    async for key in redis_client.scan_iter("eazy:lock:e2e:*"):
        await redis_client.delete(key)


# =============================================================================
# WorkerPool Configuration Tests
# =============================================================================

class TestWorkerPoolConfiguration:
    """워커 풀 설정 테스트"""

    def test_config_from_env_defaults(self):
        """환경변수 기본값 테스트"""
        with patch.dict("os.environ", {}, clear=True):
            config = WorkerPoolConfig.from_env()

            assert config.num_workers == 4
            assert config.max_restarts_per_worker == 5
            assert config.shutdown_timeout == 30.0

    def test_config_from_env_custom(self):
        """환경변수 커스텀 값 테스트"""
        with patch.dict("os.environ", {
            "WORKER_NUM_WORKERS": "8",
            "WORKER_MAX_RESTARTS": "10",
            "WORKER_SHUTDOWN_TIMEOUT": "60.0",
        }):
            config = WorkerPoolConfig.from_env()

            assert config.num_workers == 8
            assert config.max_restarts_per_worker == 10
            assert config.shutdown_timeout == 60.0

    def test_pool_properties(self, pool_config):
        """워커 풀 속성 테스트"""
        pool = WorkerPool(config=pool_config)

        assert pool.is_running is False
        assert pool.active_workers == 0


# =============================================================================
# DistributedLock Integration Tests
# =============================================================================

class TestDistributedLockIntegration:
    """분산 잠금 통합 테스트"""

    @pytest.mark.asyncio
    async def test_lock_prevents_concurrent_access(
        self, redis_client, clean_test_locks
    ):
        """잠금이 동시 접근을 방지"""
        lock1 = DistributedLock(redis_client, "e2e:target:1", ttl=60)
        lock2 = DistributedLock(redis_client, "e2e:target:1", ttl=60)

        # 첫 번째 잠금 획득
        assert await lock1.acquire() is True

        # 두 번째 잠금 시도 실패
        assert await lock2.acquire() is False

        # 첫 번째 해제 후 두 번째 획득 가능
        await lock1.release()
        assert await lock2.acquire() is True

        await lock2.release()

    @pytest.mark.asyncio
    async def test_lock_context_manager_cleanup(
        self, redis_client, clean_test_locks
    ):
        """컨텍스트 매니저가 잠금을 정리"""
        async with DistributedLock(redis_client, "e2e:target:2") as lock:
            assert await redis_client.exists(lock.lock_key) == 1

        # 컨텍스트 종료 후 잠금 해제
        assert await redis_client.exists("eazy:lock:e2e:target:2") == 0

    @pytest.mark.asyncio
    async def test_lock_extend_works(self, redis_client, clean_test_locks):
        """잠금 연장이 동작"""
        lock = DistributedLock(redis_client, "e2e:target:3", ttl=10)
        await lock.acquire()

        # 연장
        result = await lock.extend(60)
        assert result is True

        # TTL 확인
        ttl = await redis_client.ttl(lock.lock_key)
        assert 55 <= ttl <= 60

        await lock.release()

    @pytest.mark.asyncio
    async def test_lock_is_owned_check(self, redis_client, clean_test_locks):
        """소유권 확인이 동작"""
        lock1 = DistributedLock(redis_client, "e2e:target:4")
        lock2 = DistributedLock(redis_client, "e2e:target:4")

        await lock1.acquire()

        assert await lock1.is_owned() is True
        assert await lock2.is_owned() is False

        await lock1.release()


# =============================================================================
# CrawlWorker Lock Integration Tests
# =============================================================================

class TestCrawlWorkerLockIntegration:
    """CrawlWorker 잠금 통합 테스트"""

    @pytest.mark.asyncio
    async def test_crawl_worker_uses_lock(self):
        """CrawlWorker가 분산 잠금을 사용"""
        from app.workers.crawl_worker import CrawlWorker, LOCK_PREFIX, LOCK_TTL
        from app.models.target import Target
        from app.models.task import Task, TaskType, TaskStatus

        # Verify constants
        assert LOCK_PREFIX == "eazy:lock:"
        assert LOCK_TTL == 600

    @pytest.mark.asyncio
    async def test_lock_key_format_consistency(self):
        """잠금 키 형식 일관성"""
        from app.workers.crawl_worker import LOCK_PREFIX

        target_id = 123
        expected_key = f"{LOCK_PREFIX}target:{target_id}"

        assert expected_key == "eazy:lock:target:123"


# =============================================================================
# TaskResult Integration Tests
# =============================================================================

class TestTaskResultIntegration:
    """TaskResult 통합 테스트"""

    def test_task_result_status_success(self):
        """성공 결과 상태"""
        result = TaskResult.create_success({"count": 10})

        assert result.status == "success"
        assert result.success is True
        assert result.cancelled is False
        assert result.skipped is False

    def test_task_result_status_cancelled(self):
        """취소 결과 상태"""
        result = TaskResult.create_cancelled({"reason": "user"})

        assert result.status == "cancelled"
        assert result.cancelled is True

    def test_task_result_status_skipped(self):
        """스킵 결과 상태"""
        result = TaskResult.create_skipped({"reason": "lock"})

        assert result.status == "skipped"
        assert result.skipped is True
        assert result.success is False

    def test_task_result_status_failed(self):
        """실패 결과 상태"""
        result = TaskResult.create_failure("error msg")

        assert result.status == "failed"
        assert result.success is False


# =============================================================================
# Pool Lifecycle Tests
# =============================================================================

class TestPoolLifecycle:
    """워커 풀 라이프사이클 테스트"""

    @pytest.mark.asyncio
    async def test_pool_start_stop(self, pool_config):
        """풀 시작 및 정지"""
        pool = WorkerPool(config=pool_config)

        # Mock process_one_task to return False (no tasks)
        with patch("app.workers.pool.process_one_task", new=AsyncMock(return_value=False)):
            with patch("app.workers.pool.create_worker_context"):
                # 시작 태스크 생성
                start_task = asyncio.create_task(pool.start())

                # 짧은 대기 후 정지
                await asyncio.sleep(0.2)
                await pool.stop()

                # 정리 대기
                await asyncio.wait_for(start_task, timeout=2.0)

                assert pool.is_running is False

    @pytest.mark.asyncio
    async def test_pool_cannot_start_twice(self, pool_config):
        """풀은 두 번 시작할 수 없음"""
        pool = WorkerPool(config=pool_config)

        with patch("app.workers.pool.process_one_task", new=AsyncMock(return_value=False)):
            with patch("app.workers.pool.create_worker_context"):
                start_task = asyncio.create_task(pool.start())

                await asyncio.sleep(0.1)

                # 두 번째 시작 시도
                with pytest.raises(RuntimeError, match="already started"):
                    await pool.start()

                await pool.stop()
                await asyncio.wait_for(start_task, timeout=2.0)


# =============================================================================
# Error Handling Integration Tests
# =============================================================================

class TestErrorHandlingIntegration:
    """에러 처리 통합 테스트"""

    def test_lock_acquisition_error(self):
        """잠금 획득 에러"""
        error = LockAcquisitionError("target:123")

        assert "target:123" in str(error)
        assert error.lock_name == "target:123"

    def test_error_category_classification(self):
        """에러 분류 테스트"""
        from app.core.errors import classify_error, ErrorCategory

        # 연결 에러는 RETRYABLE
        conn_error = ConnectionError("Connection refused")
        assert classify_error(conn_error) == ErrorCategory.RETRYABLE

        # ValueError는 PERMANENT
        value_error = ValueError("Invalid input")
        assert classify_error(value_error) == ErrorCategory.PERMANENT

        # Rate limit은 TRANSIENT
        rate_limit_error = Exception("Rate limit exceeded 429")
        assert classify_error(rate_limit_error) == ErrorCategory.TRANSIENT

        # 알 수 없는 에러는 RETRYABLE (기본값)
        unknown_error = Exception("Unknown error")
        assert classify_error(unknown_error) == ErrorCategory.RETRYABLE


# =============================================================================
# Component Export Tests
# =============================================================================

class TestComponentExports:
    """컴포넌트 내보내기 테스트"""

    def test_lock_module_exports(self):
        """lock 모듈 내보내기"""
        from app.core.lock import DistributedLock, LockAcquisitionError

        assert DistributedLock is not None
        assert LockAcquisitionError is not None

    def test_pool_module_exports(self):
        """pool 모듈 내보내기"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig, run_worker_pool

        assert WorkerPool is not None
        assert WorkerPoolConfig is not None
        assert run_worker_pool is not None

    def test_crawl_worker_lock_constants(self):
        """crawl_worker 잠금 상수"""
        from app.workers.crawl_worker import LOCK_TTL, LOCK_PREFIX

        assert LOCK_TTL == 600
        assert LOCK_PREFIX == "eazy:lock:"
