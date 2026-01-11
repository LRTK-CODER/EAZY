"""
Phase 4: 분산 잠금 테스트
TDD RED 단계 - DistributedLock 구현 전에 모두 실패해야 함

Day 3: 분산 잠금 시스템
"""

import asyncio
import pytest
from redis.asyncio import Redis


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def redis_client() -> Redis:
    """테스트용 Redis 클라이언트"""
    from app.core.config import settings

    redis = Redis.from_url(
        settings.REDIS_URL, decode_responses=True, single_connection_client=True
    )
    # Initialize connection (required for single_connection_client in redis-py 7.x)
    await redis.ping()
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_locks(redis_client: Redis):
    """테스트 전후 잠금 정리"""
    # 테스트 전 정리
    async for key in redis_client.scan_iter("eazy:lock:test:*"):
        await redis_client.delete(key)

    yield

    # 테스트 후 정리
    async for key in redis_client.scan_iter("eazy:lock:test:*"):
        await redis_client.delete(key)


# =============================================================================
# Lock Acquisition Tests
# =============================================================================


class TestLockAcquisition:
    """잠금 획득 테스트"""

    @pytest.mark.asyncio
    async def test_acquire_succeeds_when_not_locked(
        self, redis_client: Redis, clean_locks
    ):
        """잠금이 없을 때 획득 성공"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:1")

        result = await lock.acquire()

        assert result is True
        assert await redis_client.exists("eazy:lock:test:target:1") == 1

    @pytest.mark.asyncio
    async def test_acquire_fails_when_already_locked(
        self, redis_client: Redis, clean_locks
    ):
        """이미 잠금이 있을 때 획득 실패"""
        from app.core.lock import DistributedLock

        lock1 = DistributedLock(redis_client, "test:target:2")
        lock2 = DistributedLock(redis_client, "test:target:2")

        await lock1.acquire()
        result = await lock2.acquire()

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_sets_ttl(self, redis_client: Redis, clean_locks):
        """획득 시 TTL이 설정되어야 함"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:3", ttl=60)

        await lock.acquire()

        ttl = await redis_client.ttl("eazy:lock:test:target:3")
        assert 55 <= ttl <= 60


# =============================================================================
# Lock Release Tests
# =============================================================================


class TestLockRelease:
    """잠금 해제 테스트"""

    @pytest.mark.asyncio
    async def test_release_removes_lock(self, redis_client: Redis, clean_locks):
        """해제 시 잠금 제거"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:4")
        await lock.acquire()

        result = await lock.release()

        assert result is True
        assert await redis_client.exists("eazy:lock:test:target:4") == 0

    @pytest.mark.asyncio
    async def test_release_fails_for_wrong_owner(
        self, redis_client: Redis, clean_locks
    ):
        """다른 소유자의 잠금은 해제 불가"""
        from app.core.lock import DistributedLock

        lock1 = DistributedLock(redis_client, "test:target:5")
        lock2 = DistributedLock(redis_client, "test:target:5")

        await lock1.acquire()
        result = await lock2.release()  # lock2는 획득하지 않음

        assert result is False
        # lock1의 잠금은 여전히 존재
        assert await redis_client.exists("eazy:lock:test:target:5") == 1

    @pytest.mark.asyncio
    async def test_release_after_expiry_returns_false(
        self, redis_client: Redis, clean_locks
    ):
        """만료 후 해제 시도는 False 반환"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:6", ttl=1)
        await lock.acquire()

        await asyncio.sleep(1.5)  # TTL 만료 대기
        result = await lock.release()

        assert result is False


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Context Manager 테스트"""

    @pytest.mark.asyncio
    async def test_context_manager_acquires_and_releases(
        self, redis_client: Redis, clean_locks
    ):
        """with 블록 진입/종료 시 획득/해제"""
        from app.core.lock import DistributedLock

        async with DistributedLock(redis_client, "test:target:7") as _:
            assert await redis_client.exists("eazy:lock:test:target:7") == 1

        assert await redis_client.exists("eazy:lock:test:target:7") == 0

    @pytest.mark.asyncio
    async def test_context_manager_raises_on_failure(
        self, redis_client: Redis, clean_locks
    ):
        """획득 실패 시 예외 발생"""
        from app.core.lock import DistributedLock, LockAcquisitionError

        lock1 = DistributedLock(redis_client, "test:target:8")
        await lock1.acquire()

        with pytest.raises(LockAcquisitionError) as exc_info:
            async with DistributedLock(redis_client, "test:target:8"):
                pass

        assert "test:target:8" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_context_manager_releases_on_exception(
        self, redis_client: Redis, clean_locks
    ):
        """예외 발생 시에도 잠금 해제"""
        from app.core.lock import DistributedLock

        try:
            async with DistributedLock(redis_client, "test:target:9"):
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert await redis_client.exists("eazy:lock:test:target:9") == 0


# =============================================================================
# Lock Extension Tests
# =============================================================================


class TestLockExtension:
    """TTL 연장 테스트"""

    @pytest.mark.asyncio
    async def test_extend_increases_ttl(self, redis_client: Redis, clean_locks):
        """extend 호출 시 TTL 증가"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:10", ttl=10)
        await lock.acquire()

        result = await lock.extend(60)

        assert result is True
        ttl = await redis_client.ttl("eazy:lock:test:target:10")
        assert 55 <= ttl <= 60

    @pytest.mark.asyncio
    async def test_extend_fails_for_wrong_owner(self, redis_client: Redis, clean_locks):
        """다른 소유자의 잠금은 연장 불가"""
        from app.core.lock import DistributedLock

        lock1 = DistributedLock(redis_client, "test:target:11")
        lock2 = DistributedLock(redis_client, "test:target:11")

        await lock1.acquire()
        result = await lock2.extend(60)

        assert result is False


# =============================================================================
# Concurrency Tests
# =============================================================================


class TestConcurrency:
    """동시성 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_acquire_only_one_succeeds(
        self, redis_client: Redis, clean_locks
    ):
        """동시 획득 시도 시 하나만 성공"""
        from app.core.lock import DistributedLock

        results = []

        async def try_acquire(lock_id: int):
            lock = DistributedLock(redis_client, "test:target:12")
            result = await lock.acquire()
            results.append((lock_id, result))

        await asyncio.gather(try_acquire(1), try_acquire(2), try_acquire(3))

        success_count = sum(1 for _, r in results if r)
        assert success_count == 1

    @pytest.mark.asyncio
    async def test_sequential_locks_work(self, redis_client: Redis, clean_locks):
        """순차적 잠금/해제가 정상 동작"""
        from app.core.lock import DistributedLock

        for i in range(3):
            lock = DistributedLock(redis_client, "test:target:13")
            assert await lock.acquire() is True
            assert await lock.release() is True


# =============================================================================
# Is Owned Tests
# =============================================================================


class TestIsOwned:
    """소유권 확인 테스트"""

    @pytest.mark.asyncio
    async def test_is_owned_returns_true_for_owner(
        self, redis_client: Redis, clean_locks
    ):
        """소유자에게 True 반환"""
        from app.core.lock import DistributedLock

        lock = DistributedLock(redis_client, "test:target:14")
        await lock.acquire()

        assert await lock.is_owned() is True

    @pytest.mark.asyncio
    async def test_is_owned_returns_false_for_non_owner(
        self, redis_client: Redis, clean_locks
    ):
        """비소유자에게 False 반환"""
        from app.core.lock import DistributedLock

        lock1 = DistributedLock(redis_client, "test:target:15")
        lock2 = DistributedLock(redis_client, "test:target:15")

        await lock1.acquire()

        assert await lock2.is_owned() is False


# =============================================================================
# Lock Info Tests
# =============================================================================


class TestLockInfo:
    """잠금 정보 테스트"""

    def test_lock_key_format(self):
        """잠금 키 형식 확인"""
        from app.core.lock import DistributedLock
        from unittest.mock import MagicMock

        mock_redis = MagicMock()
        lock = DistributedLock(mock_redis, "target:123")

        assert lock.lock_key == "eazy:lock:target:123"

    def test_custom_prefix(self):
        """커스텀 접두사 확인"""
        from app.core.lock import DistributedLock
        from unittest.mock import MagicMock

        mock_redis = MagicMock()
        lock = DistributedLock(mock_redis, "target:456", prefix="custom:")

        assert lock.lock_key == "custom:target:456"

    def test_token_is_unique(self):
        """토큰이 고유한지 확인"""
        from app.core.lock import DistributedLock
        from unittest.mock import MagicMock

        mock_redis = MagicMock()
        lock1 = DistributedLock(mock_redis, "target:789")
        lock2 = DistributedLock(mock_redis, "target:789")

        assert lock1.token != lock2.token
