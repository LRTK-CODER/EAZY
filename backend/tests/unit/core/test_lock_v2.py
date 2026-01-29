"""
Unit tests for DistributedLockV2 (TDD RED Phase)

These tests are written BEFORE implementation to drive the design.
They will fail until app/core/lock_v2.py is implemented.
"""

from unittest.mock import AsyncMock

import pytest

# Import will fail until module is implemented - this is expected in TDD RED phase
try:
    from app.core.lock_v2 import DistributedLockV2, LockLevel
except ImportError:
    pytest.skip("lock_v2 module not yet implemented", allow_module_level=True)


class TestDistributedLockV2Basic:
    """Basic lock acquisition and release tests."""

    @pytest.mark.asyncio
    async def test_acquire_returns_fence_token(self):
        """획득 시 fence token 반환"""
        # Given: Redis returns a fence token
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Lock is acquired
        token = await lock.acquire()

        # Then: Fence token is returned
        assert token is not None
        assert isinstance(token, int)
        assert token > 0

    @pytest.mark.asyncio
    async def test_release_requires_matching_token(self):
        """해제 시 token 검증"""
        # Given: Lock is acquired with a token
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.get.return_value = b"1"
        redis_mock.delete.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        token = await lock.acquire()

        # When: Lock is released with correct token
        result = await lock.release(token)

        # Then: Release succeeds
        assert result is True

    @pytest.mark.asyncio
    async def test_release_fails_with_wrong_token(self):
        """잘못된 token으로 해제 실패"""
        # Given: Lock is acquired
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 0  # Token mismatch

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        await lock.acquire()

        # When: Lock is released with wrong token
        result = await lock.release(999)

        # Then: Release fails
        assert result is False


class TestDistributedLockV2Concurrency:
    """Concurrent lock acquisition tests."""

    @pytest.mark.asyncio
    async def test_only_one_can_acquire(self):
        """동시 획득 시 하나만 성공"""
        # Given: Redis SET NX behavior (only first succeeds)
        redis_mock = AsyncMock()

        call_count = 0

        async def mock_set(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # Only first call succeeds

        redis_mock.set.side_effect = mock_set
        redis_mock.incr.return_value = 1

        lock1 = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        lock2 = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Two locks try to acquire simultaneously
        token1 = await lock1.acquire()
        token2 = await lock2.acquire()

        # Then: Only one succeeds
        assert token1 is not None
        assert token2 is None

    @pytest.mark.asyncio
    async def test_acquire_with_timeout(self):
        """타임아웃 내 획득 재시도"""
        # Given: Lock is held by another process, then released
        redis_mock = AsyncMock()

        call_count = 0

        async def mock_set(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Succeeds on 3rd attempt

        redis_mock.set.side_effect = mock_set
        redis_mock.incr.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Acquire with timeout and retry
        token = await lock.acquire(timeout=2.0, retry_interval=0.5)

        # Then: Eventually succeeds
        assert token is not None
        assert call_count >= 3

    @pytest.mark.asyncio
    async def test_acquire_timeout_expires(self):
        """타임아웃 초과 시 None 반환"""
        # Given: Lock is always held
        redis_mock = AsyncMock()
        redis_mock.set.return_value = False

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Acquire with short timeout
        token = await lock.acquire(timeout=0.5, retry_interval=0.1)

        # Then: Returns None after timeout
        assert token is None


class TestDistributedLockV2Renewal:
    """Lock renewal and TTL extension tests."""

    @pytest.mark.asyncio
    async def test_lock_renewal_extends_ttl(self):
        """갱신 시 TTL 연장"""
        # Given: Lock is acquired
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 1  # Renewal success

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        token = await lock.acquire()

        # When: Lock is renewed
        result = await lock.renew(token, ttl_seconds=60)

        # Then: TTL is extended
        assert result is True
        redis_mock.eval.assert_called()

    @pytest.mark.asyncio
    async def test_renewal_fails_with_wrong_token(self):
        """잘못된 token으로 갱신 실패"""
        # Given: Lock is acquired
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 0  # Token mismatch

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        await lock.acquire()

        # When: Renewal attempted with wrong token
        result = await lock.renew(999, ttl_seconds=60)

        # Then: Renewal fails
        assert result is False

    @pytest.mark.asyncio
    async def test_renewal_fails_after_expiry(self):
        """만료 후 갱신 실패"""
        # Given: Lock has expired
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 0  # Lock expired

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        token = await lock.acquire()

        # When: Renewal attempted after expiry
        result = await lock.renew(token, ttl_seconds=60)

        # Then: Renewal fails
        assert result is False


class TestDistributedLockV2FenceToken:
    """Fence token monotonicity tests."""

    @pytest.mark.asyncio
    async def test_fence_token_increases_monotonically(self):
        """fence token 단조 증가"""
        # Given: Redis incr returns increasing values
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True

        tokens = [1, 2, 3, 4, 5]
        redis_mock.incr.side_effect = tokens

        # When: Multiple locks are acquired
        acquired_tokens = []
        for i in range(5):
            lock = DistributedLockV2(
                redis=redis_mock,
                resource_id=f"resource-{i}",
                level=LockLevel.TASK,
                ttl_seconds=30,
            )
            token = await lock.acquire()
            acquired_tokens.append(token)

        # Then: Tokens increase monotonically
        assert acquired_tokens == tokens
        for i in range(len(acquired_tokens) - 1):
            assert acquired_tokens[i] < acquired_tokens[i + 1]

    @pytest.mark.asyncio
    async def test_fence_token_persists_across_instances(self):
        """인스턴스 간 fence token 지속성"""
        # Given: Redis incr counter persists
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.side_effect = [5, 6]  # Counter already at 5

        # When: New lock instances acquire
        lock1 = DistributedLockV2(
            redis=redis_mock,
            resource_id="resource-1",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )
        token1 = await lock1.acquire()

        lock2 = DistributedLockV2(
            redis=redis_mock,
            resource_id="resource-2",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )
        token2 = await lock2.acquire()

        # Then: Tokens continue from persisted counter
        assert token1 == 5
        assert token2 == 6


class TestDistributedLockV2ContextManager:
    """Context manager (__aenter__/__aexit__) tests."""

    @pytest.mark.asyncio
    async def test_context_manager_acquires_and_releases(self):
        """컨텍스트 매니저로 획득 및 해제"""
        # Given: Redis mock
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 1  # Release success

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Used as context manager
        async with lock as token:
            # Then: Lock is acquired
            assert token is not None
            assert isinstance(token, int)

        # Then: Lock is released after context
        redis_mock.eval.assert_called()

    @pytest.mark.asyncio
    async def test_context_manager_releases_on_exception(self):
        """예외 발생 시에도 해제"""
        # Given: Redis mock
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.eval.return_value = 1  # Release success

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Exception occurs in context
        with pytest.raises(ValueError):
            async with lock:
                raise ValueError("Test exception")

        # Then: Lock is still released
        redis_mock.eval.assert_called()

    @pytest.mark.asyncio
    async def test_context_manager_fails_to_acquire(self):
        """획득 실패 시 컨텍스트 진입 불가"""
        # Given: Lock acquisition fails
        redis_mock = AsyncMock()
        redis_mock.set.return_value = False

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When/Then: Context manager raises exception
        with pytest.raises(RuntimeError, match="Failed to acquire lock"):
            async with lock:
                pass


class TestDistributedLockV2Levels:
    """Lock level (TASK, URL, TARGET) tests."""

    @pytest.mark.asyncio
    async def test_task_level_lock(self):
        """TASK 레벨 락 키 생성"""
        # Given: TASK level lock
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="task-123",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Lock is acquired
        await lock.acquire()

        # Then: Correct Redis key is used
        call_args = redis_mock.set.call_args
        assert "lock:task:task-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_url_level_lock(self):
        """URL 레벨 락 키 생성"""
        # Given: URL level lock
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="https://example.com/page",
            level=LockLevel.URL,
            ttl_seconds=30,
        )

        # When: Lock is acquired
        await lock.acquire()

        # Then: Correct Redis key is used
        call_args = redis_mock.set.call_args
        assert "lock:url:" in str(call_args)

    @pytest.mark.asyncio
    async def test_target_level_lock(self):
        """TARGET 레벨 락 키 생성"""
        # Given: TARGET level lock
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="target-456",
            level=LockLevel.TARGET,
            ttl_seconds=30,
        )

        # When: Lock is acquired
        await lock.acquire()

        # Then: Correct Redis key is used
        call_args = redis_mock.set.call_args
        assert "lock:target:target-456" in str(call_args)

    @pytest.mark.asyncio
    async def test_different_levels_dont_conflict(self):
        """다른 레벨의 락은 충돌하지 않음"""
        # Given: Same resource_id, different levels
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.side_effect = [1, 2]

        lock_task = DistributedLockV2(
            redis=redis_mock,
            resource_id="resource-1",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        lock_url = DistributedLockV2(
            redis=redis_mock,
            resource_id="resource-1",
            level=LockLevel.URL,
            ttl_seconds=30,
        )

        # When: Both locks acquire
        token1 = await lock_task.acquire()
        token2 = await lock_url.acquire()

        # Then: Both succeed (different Redis keys)
        assert token1 is not None
        assert token2 is not None
        assert redis_mock.set.call_count == 2


class TestDistributedLockV2EdgeCases:
    """Edge cases and error handling tests."""

    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Redis 연결 오류 처리"""
        # Given: Redis raises connection error
        redis_mock = AsyncMock()
        redis_mock.set.side_effect = ConnectionError("Redis unavailable")

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When/Then: Acquire propagates error
        with pytest.raises(ConnectionError):
            await lock.acquire()

    @pytest.mark.asyncio
    async def test_release_nonexistent_lock(self):
        """존재하지 않는 락 해제"""
        # Given: Lock was never acquired
        redis_mock = AsyncMock()
        redis_mock.eval.return_value = 0  # Lock doesn't exist

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        # When: Release without acquire
        result = await lock.release(1)

        # Then: Returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_ttl_zero_or_negative(self):
        """잘못된 TTL 값 처리"""
        # Given: Invalid TTL
        redis_mock = AsyncMock()

        # When/Then: Constructor raises error
        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            DistributedLockV2(
                redis=redis_mock,
                resource_id="test-resource",
                level=LockLevel.TASK,
                ttl_seconds=0,
            )

    @pytest.mark.asyncio
    async def test_empty_resource_id(self):
        """빈 resource_id 처리"""
        # Given: Empty resource_id
        redis_mock = AsyncMock()

        # When/Then: Constructor raises error
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            DistributedLockV2(
                redis=redis_mock, resource_id="", level=LockLevel.TASK, ttl_seconds=30
            )

    @pytest.mark.asyncio
    async def test_get_lock_info(self):
        """락 정보 조회"""
        # Given: Lock is acquired
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 42
        redis_mock.get.return_value = b"42"
        redis_mock.ttl.return_value = 25

        lock = DistributedLockV2(
            redis=redis_mock,
            resource_id="test-resource",
            level=LockLevel.TASK,
            ttl_seconds=30,
        )

        await lock.acquire()

        # When: Lock info is queried
        info = await lock.get_info()

        # Then: Info contains correct data
        assert info["resource_id"] == "test-resource"
        assert info["level"] == LockLevel.TASK
        assert info["current_token"] == 42
        assert info["ttl"] == 25
        assert info["is_locked"] is True
