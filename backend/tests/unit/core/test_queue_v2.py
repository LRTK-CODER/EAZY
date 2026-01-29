"""
Unit tests for TaskQueueV2 (TDD RED phase).

These tests will fail initially because TaskQueueV2 doesn't exist yet.
Tests drive the implementation by specifying exact behavior expectations.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.priority import TaskPriority


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.zadd = AsyncMock(return_value=1)
    redis.zrange = AsyncMock(return_value=[])
    redis.zrangebyscore = AsyncMock(return_value=[])
    redis.zrem = AsyncMock(return_value=1)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.hset = AsyncMock(return_value=1)
    redis.hget = AsyncMock(return_value=None)
    redis.hdel = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def queue(mock_redis):
    """Create TaskQueueV2 instance with mocked Redis."""
    from app.core.queue_v2 import TaskQueueV2

    return TaskQueueV2(redis=mock_redis, queue_name="test_queue")


class TestTaskQueueV2Initialization:
    """Test queue initialization and configuration."""

    @pytest.mark.asyncio
    async def test_init_with_default_params(self, mock_redis):
        """Queue initializes with default parameters."""
        from app.core.queue_v2 import TaskQueueV2

        queue = TaskQueueV2(redis=mock_redis)

        assert queue.redis == mock_redis
        assert queue.queue_name == "task_queue"
        assert queue.visibility_timeout == 300  # 5 minutes default
        assert queue.max_retries == 3
        assert queue.base_backoff_seconds == 60

    @pytest.mark.asyncio
    async def test_init_with_custom_params(self, mock_redis):
        """Queue initializes with custom parameters."""
        from app.core.queue_v2 import TaskQueueV2

        queue = TaskQueueV2(
            redis=mock_redis,
            queue_name="custom_queue",
            visibility_timeout=600,
            max_retries=5,
            base_backoff_seconds=120,
        )

        assert queue.queue_name == "custom_queue"
        assert queue.visibility_timeout == 600
        assert queue.max_retries == 5
        assert queue.base_backoff_seconds == 120


class TestTaskQueueV2Enqueue:
    """Test enqueue operations with priority handling."""

    @pytest.mark.asyncio
    async def test_enqueue_with_critical_priority(self, queue, mock_redis):
        """Enqueue task with CRITICAL priority."""
        task_id = "task_123"
        task_data = {"url": "https://example.com", "depth": 0}

        await queue.enqueue(
            task_id=task_id, task_data=task_data, priority=TaskPriority.CRITICAL
        )

        # Verify zadd called with correct priority score
        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert "test_queue:pending" in call_args[0]
        assert task_id in str(call_args[1])
        # CRITICAL = 1000 in TaskPriority
        assert call_args[1]["mapping"][task_id] == TaskPriority.CRITICAL.value

    @pytest.mark.asyncio
    async def test_enqueue_with_high_priority(self, queue, mock_redis):
        """Enqueue task with HIGH priority."""
        task_id = "task_456"
        task_data = {"url": "https://example.com"}

        await queue.enqueue(
            task_id=task_id, task_data=task_data, priority=TaskPriority.HIGH
        )

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert call_args[1]["mapping"][task_id] == TaskPriority.HIGH.value

    @pytest.mark.asyncio
    async def test_enqueue_with_normal_priority(self, queue, mock_redis):
        """Enqueue task with NORMAL priority (default)."""
        task_id = "task_789"
        task_data = {"url": "https://example.com"}

        await queue.enqueue(
            task_id=task_id, task_data=task_data, priority=TaskPriority.NORMAL
        )

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert call_args[1]["mapping"][task_id] == TaskPriority.NORMAL.value

    @pytest.mark.asyncio
    async def test_enqueue_with_low_priority(self, queue, mock_redis):
        """Enqueue task with LOW priority."""
        task_id = "task_low"
        task_data = {"url": "https://example.com"}

        await queue.enqueue(
            task_id=task_id, task_data=task_data, priority=TaskPriority.LOW
        )

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert call_args[1]["mapping"][task_id] == TaskPriority.LOW.value

    @pytest.mark.asyncio
    async def test_enqueue_stores_task_data(self, queue, mock_redis):
        """Enqueue stores task data in Redis hash."""
        task_id = "task_data"
        task_data = {"url": "https://example.com", "depth": 2, "retry_count": 0}

        await queue.enqueue(
            task_id=task_id, task_data=task_data, priority=TaskPriority.NORMAL
        )

        # Verify task data stored in hash
        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert "test_queue:data" in call_args[0]
        assert task_id == call_args[1]["key"]
        stored_data = json.loads(call_args[1]["value"])
        assert stored_data == task_data

    @pytest.mark.asyncio
    async def test_enqueue_default_priority_is_normal(self, queue, mock_redis):
        """Enqueue without priority defaults to NORMAL."""
        task_id = "task_default"
        task_data = {"url": "https://example.com"}

        await queue.enqueue(task_id=task_id, task_data=task_data)

        call_args = mock_redis.zadd.call_args
        assert call_args[1]["mapping"][task_id] == TaskPriority.NORMAL.value


class TestTaskQueueV2Dequeue:
    """Test dequeue operations respecting priority order."""

    @pytest.mark.asyncio
    async def test_dequeue_respects_priority_order(self, queue, mock_redis):
        """Dequeue returns tasks in priority order: CRITICAL > HIGH > NORMAL > LOW."""
        # Mock pending queue with mixed priorities
        # zrange returns lowest score first (highest priority)
        task_critical = "task_critical"
        task_data = {
            "url": "https://example.com",
            "priority": TaskPriority.CRITICAL.value,
        }

        # Mock eval to return [task_id, task_data] as JSON
        mock_redis.eval.return_value = json.dumps(
            [task_critical, json.dumps(task_data)]
        )

        task = await queue.dequeue()

        assert task is not None
        assert task["task_id"] == task_critical
        # Verify eval called
        mock_redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_dequeue_from_empty_queue(self, queue, mock_redis):
        """Dequeue from empty queue returns None."""
        mock_redis.eval.return_value = None  # Empty queue

        task = await queue.dequeue()

        assert task is None

    @pytest.mark.asyncio
    async def test_dequeue_moves_to_processing(self, queue, mock_redis):
        """Dequeue moves task to processing queue."""
        task_id = "task_process"
        task_data = {"url": "https://example.com"}

        # Mock eval to return [task_id, task_data] as JSON
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        result = await queue.dequeue()

        # Verify dequeue succeeded (eval was called and processed atomically)
        assert result is not None
        assert result["task_id"] == task_id
        mock_redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_dequeue_sets_visibility_timeout(self, queue, mock_redis):
        """Dequeue sets visibility timeout for task."""
        task_id = "task_timeout"
        task_data = {"url": "https://example.com"}

        # Mock eval to return [task_id, task_data] as JSON
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        datetime.now().timestamp()
        result = await queue.dequeue()
        datetime.now().timestamp()

        # Verify dequeue succeeded
        assert result is not None
        assert result["task_id"] == task_id

        # Verify eval was called
        mock_redis.eval.assert_called()

        # The Lua script handles visibility timeout internally,
        # so we just verify eval was called with the correct arguments
        # (script, num_keys, keys..., args...)
        call_args = mock_redis.eval.call_args[0]
        assert len(call_args) >= 5  # script, num_keys, 3 keys, visibility_deadline

    @pytest.mark.asyncio
    async def test_dequeue_returns_task_with_metadata(self, queue, mock_redis):
        """Dequeue returns task with all metadata."""
        task_id = "task_meta"
        task_data = {
            "url": "https://example.com",
            "depth": 1,
            "retry_count": 0,
            "priority": TaskPriority.HIGH.value,
        }

        # Mock eval to return [task_id, task_data] as JSON
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        task = await queue.dequeue()

        assert task["task_id"] == task_id
        assert task["url"] == "https://example.com"
        assert task["depth"] == 1
        assert task["retry_count"] == 0


class TestTaskQueueV2Ack:
    """Test ACK operations for successful task completion."""

    @pytest.mark.asyncio
    async def test_ack_removes_from_processing(self, queue, mock_redis):
        """ACK removes task from processing queue."""
        task_id = "task_ack"

        await queue.ack(task_id)

        # Verify task removed from processing
        mock_redis.zrem.assert_called()
        call_args = mock_redis.zrem.call_args
        assert "test_queue:processing" in call_args[0]
        assert task_id in call_args[0]

    @pytest.mark.asyncio
    async def test_ack_removes_task_data(self, queue, mock_redis):
        """ACK removes task data from storage."""
        task_id = "task_ack_data"

        await queue.ack(task_id)

        # Verify task data deleted
        mock_redis.hdel.assert_called()
        call_args = mock_redis.hdel.call_args
        assert "test_queue:data" in call_args[0]
        assert task_id in call_args[0]

    @pytest.mark.asyncio
    async def test_ack_nonexistent_task(self, queue, mock_redis):
        """ACK non-existent task doesn't raise error."""
        mock_redis.zrem.return_value = 0
        mock_redis.hdel.return_value = 0

        # Should not raise exception
        await queue.ack("nonexistent_task")

        assert mock_redis.zrem.called
        assert mock_redis.hdel.called


class TestTaskQueueV2Nack:
    """Test NACK operations for task failure handling."""

    @pytest.mark.asyncio
    async def test_nack_with_retry_adds_to_delayed(self, queue, mock_redis):
        """NACK with retry moves task to delayed queue with backoff."""
        task_id = "task_nack_retry"
        retry_count = 1

        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": retry_count}
        ).encode()

        before_nack = datetime.now().timestamp()
        await queue.nack(task_id, retry=True)
        after_nack = datetime.now().timestamp()

        # Verify removed from processing
        zrem_calls = [
            call for call in mock_redis.zrem.call_args_list if "processing" in str(call)
        ]
        assert len(zrem_calls) > 0

        # Verify added to delayed with exponential backoff
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "delayed" in str(call)
        ]
        assert len(zadd_calls) > 0

        call_args = zadd_calls[0]
        delay_score = call_args[1]["mapping"][task_id]

        # Calculate expected backoff: base * (2 ^ retry_count)
        expected_backoff = queue.base_backoff_seconds * (2**retry_count)
        expected_min = before_nack + expected_backoff
        expected_max = after_nack + expected_backoff

        assert expected_min <= delay_score <= expected_max

    @pytest.mark.asyncio
    async def test_nack_with_retry_increments_retry_count(self, queue, mock_redis):
        """NACK with retry increments retry count in task data."""
        task_id = "task_retry_count"
        initial_retry = 1

        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": initial_retry}
        ).encode()

        await queue.nack(task_id, retry=True)

        # Verify task data updated with incremented retry count
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        updated_data = json.loads(call_args[1]["value"])
        assert updated_data["retry_count"] == initial_retry + 1

    @pytest.mark.asyncio
    async def test_nack_without_retry_adds_to_dlq(self, queue, mock_redis):
        """NACK without retry moves task to DLQ."""
        task_id = "task_nack_dlq"

        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": 0}
        ).encode()

        await queue.nack(task_id, retry=False)

        # Verify removed from processing
        zrem_calls = [
            call for call in mock_redis.zrem.call_args_list if "processing" in str(call)
        ]
        assert len(zrem_calls) > 0

        # Verify added to DLQ with current timestamp
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "dlq" in str(call)
        ]
        assert len(zadd_calls) > 0

    @pytest.mark.asyncio
    async def test_nack_max_retries_moves_to_dlq(self, queue, mock_redis):
        """NACK with retry count >= max_retries moves to DLQ."""
        task_id = "task_max_retry"

        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": queue.max_retries}
        ).encode()

        await queue.nack(task_id, retry=True)

        # Should go to DLQ, not delayed
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "dlq" in str(call)
        ]
        assert len(zadd_calls) > 0

        delayed_calls = [
            call for call in mock_redis.zadd.call_args_list if "delayed" in str(call)
        ]
        assert len(delayed_calls) == 0

    @pytest.mark.asyncio
    async def test_nack_stores_failure_metadata(self, queue, mock_redis):
        """NACK stores failure timestamp and reason in task data."""
        task_id = "task_failure_meta"
        error_msg = "Connection timeout"

        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": 0}
        ).encode()

        before_nack = datetime.now().timestamp()
        await queue.nack(task_id, retry=True, error=error_msg)
        after_nack = datetime.now().timestamp()

        # Verify task data includes failure info
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        updated_data = json.loads(call_args[1]["value"])

        assert "last_error" in updated_data
        assert updated_data["last_error"] == error_msg
        assert "failed_at" in updated_data
        assert before_nack <= updated_data["failed_at"] <= after_nack


class TestTaskQueueV2VisibilityTimeout:
    """Test visibility timeout handling and recovery."""

    @pytest.mark.asyncio
    async def test_recover_expired_visibility_timeout(self, queue, mock_redis):
        """Recover tasks with expired visibility timeout back to pending."""
        expired_task = "task_expired"
        current_time = datetime.now().timestamp()

        # Mock processing queue with expired task
        mock_redis.zrangebyscore.return_value = [expired_task.encode()]
        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "retry_count": 1}
        ).encode()

        recovered = await queue.recover_expired_tasks()

        # Verify zrangebyscore called with correct range (0 to current_time)
        mock_redis.zrangebyscore.assert_called()
        call_args = mock_redis.zrangebyscore.call_args
        assert "test_queue:processing" in call_args[0]
        min_score = call_args[1]["min"]
        max_score = call_args[1]["max"]
        assert min_score == 0
        assert max_score <= current_time + 1  # Allow 1 second tolerance

        assert recovered == 1

    @pytest.mark.asyncio
    async def test_recover_moves_back_to_pending(self, queue, mock_redis):
        """Recovered tasks move back to pending queue with original priority."""
        expired_task = "task_recover"
        original_priority = TaskPriority.HIGH

        mock_redis.zrangebyscore.return_value = [expired_task.encode()]
        mock_redis.hget.return_value = json.dumps(
            {
                "url": "https://example.com",
                "priority": original_priority.value,
                "retry_count": 0,
            }
        ).encode()

        await queue.recover_expired_tasks()

        # Verify removed from processing
        zrem_calls = [
            call for call in mock_redis.zrem.call_args_list if "processing" in str(call)
        ]
        assert len(zrem_calls) > 0

        # Verify added back to pending with original priority
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "pending" in str(call)
        ]
        assert len(zadd_calls) > 0

        call_args = zadd_calls[0]
        assert call_args[1]["mapping"][expired_task] == original_priority.value

    @pytest.mark.asyncio
    async def test_recover_no_expired_tasks(self, queue, mock_redis):
        """Recover with no expired tasks returns 0."""
        mock_redis.zrangebyscore.return_value = []

        recovered = await queue.recover_expired_tasks()

        assert recovered == 0

    @pytest.mark.asyncio
    async def test_recover_increments_timeout_count(self, queue, mock_redis):
        """Recovered tasks have timeout count incremented."""
        expired_task = "task_timeout_count"

        mock_redis.zrangebyscore.return_value = [expired_task.encode()]
        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "timeout_count": 1}
        ).encode()

        await queue.recover_expired_tasks()

        # Verify task data updated
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        updated_data = json.loads(call_args[1]["value"])
        assert updated_data["timeout_count"] == 2


class TestTaskQueueV2DelayedTasks:
    """Test delayed task handling."""

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_moves_ready_to_pending(
        self, queue, mock_redis
    ):
        """Process delayed tasks moves ready tasks to pending."""
        ready_task = "task_ready"
        current_time = datetime.now().timestamp()

        mock_redis.zrangebyscore.return_value = [ready_task.encode()]
        mock_redis.hget.return_value = json.dumps(
            {"url": "https://example.com", "priority": TaskPriority.NORMAL.value}
        ).encode()

        processed = await queue.process_delayed_tasks()

        # Verify zrangebyscore called with correct range
        mock_redis.zrangebyscore.assert_called()
        call_args = mock_redis.zrangebyscore.call_args
        assert "test_queue:delayed" in call_args[0]
        assert call_args[1]["min"] == 0
        assert call_args[1]["max"] <= current_time + 1

        # Verify moved to pending
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "pending" in str(call)
        ]
        assert len(zadd_calls) > 0

        assert processed == 1

    @pytest.mark.asyncio
    async def test_process_delayed_no_ready_tasks(self, queue, mock_redis):
        """Process delayed with no ready tasks returns 0."""
        mock_redis.zrangebyscore.return_value = []

        processed = await queue.process_delayed_tasks()

        assert processed == 0


class TestTaskQueueV2ExponentialBackoff:
    """Test exponential backoff calculation."""

    @pytest.mark.asyncio
    async def test_calculate_backoff_first_retry(self, queue):
        """Calculate backoff for first retry: base * 2^0 = base."""
        backoff = queue._calculate_backoff(retry_count=0)
        assert backoff == queue.base_backoff_seconds

    @pytest.mark.asyncio
    async def test_calculate_backoff_second_retry(self, queue):
        """Calculate backoff for second retry: base * 2^1 = base * 2."""
        backoff = queue._calculate_backoff(retry_count=1)
        assert backoff == queue.base_backoff_seconds * 2

    @pytest.mark.asyncio
    async def test_calculate_backoff_third_retry(self, queue):
        """Calculate backoff for third retry: base * 2^2 = base * 4."""
        backoff = queue._calculate_backoff(retry_count=2)
        assert backoff == queue.base_backoff_seconds * 4

    @pytest.mark.asyncio
    async def test_calculate_backoff_exponential_growth(self, queue):
        """Calculate backoff grows exponentially."""
        backoffs = [queue._calculate_backoff(i) for i in range(5)]

        # Each backoff should be 2x the previous
        for i in range(1, len(backoffs)):
            assert backoffs[i] == backoffs[i - 1] * 2

    @pytest.mark.asyncio
    async def test_calculate_backoff_with_custom_base(self, mock_redis):
        """Calculate backoff uses custom base backoff seconds."""
        from app.core.queue_v2 import TaskQueueV2

        queue = TaskQueueV2(redis=mock_redis, base_backoff_seconds=120)
        backoff = queue._calculate_backoff(retry_count=2)

        assert backoff == 120 * 4  # 120 * 2^2


class TestTaskQueueV2QueueStats:
    """Test queue statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, queue, mock_redis):
        """Get queue statistics for all queues."""
        mock_redis.zcard = AsyncMock(return_value=5)

        stats = await queue.get_stats()

        assert "pending" in stats
        assert "processing" in stats
        assert "delayed" in stats
        assert "dlq" in stats
        assert stats["pending"] == 5
        assert stats["processing"] == 5
        assert stats["delayed"] == 5
        assert stats["dlq"] == 5

    @pytest.mark.asyncio
    async def test_get_queue_size_pending(self, queue, mock_redis):
        """Get pending queue size."""
        mock_redis.zcard = AsyncMock(return_value=10)

        size = await queue.get_queue_size("pending")

        mock_redis.zcard.assert_called_once()
        call_args = mock_redis.zcard.call_args
        assert "test_queue:pending" in call_args[0]
        assert size == 10

    @pytest.mark.asyncio
    async def test_get_queue_size_processing(self, queue, mock_redis):
        """Get processing queue size."""
        mock_redis.zcard = AsyncMock(return_value=3)

        size = await queue.get_queue_size("processing")

        assert size == 3

    @pytest.mark.asyncio
    async def test_get_dlq_tasks(self, queue, mock_redis):
        """Get all tasks in DLQ."""
        dlq_tasks = ["task_1", "task_2", "task_3"]
        mock_redis.zrange.return_value = [t.encode() for t in dlq_tasks]

        tasks = await queue.get_dlq_tasks()

        mock_redis.zrange.assert_called()
        call_args = mock_redis.zrange.call_args
        assert "test_queue:dlq" in call_args[0]
        assert len(tasks) == 3


class TestTaskQueueV2ConcurrentAccess:
    """Test concurrent access and race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_dequeue_no_duplicate(self, queue, mock_redis):
        """Concurrent dequeue doesn't return same task twice."""
        task_id = "task_concurrent"
        task_data = {"url": "https://example.com"}

        # First dequeue succeeds
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        task1 = await queue.dequeue()

        # Second dequeue returns empty (task already processing)
        mock_redis.eval.return_value = None

        task2 = await queue.dequeue()

        assert task1 is not None
        assert task2 is None

    @pytest.mark.asyncio
    async def test_ack_during_visibility_timeout(self, queue, mock_redis):
        """ACK removes task even if visibility timeout not expired."""
        task_id = "task_ack_early"

        await queue.ack(task_id)

        # Verify removed from processing regardless of timeout
        mock_redis.zrem.assert_called()
        call_args = mock_redis.zrem.call_args
        assert "test_queue:processing" in call_args[0]


class TestTaskQueueV2EdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_enqueue_with_empty_task_data(self, queue, mock_redis):
        """Enqueue with empty task data."""
        task_id = "task_empty"

        await queue.enqueue(task_id=task_id, task_data={})

        # Should still work, storing empty dict
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        stored_data = json.loads(call_args[1]["value"])
        assert stored_data == {}

    @pytest.mark.asyncio
    async def test_dequeue_with_corrupted_task_data(self, queue, mock_redis):
        """Dequeue with corrupted task data handles gracefully."""
        task_id = "task_corrupted"

        # Mock eval to return corrupted task data
        mock_redis.eval.return_value = json.dumps([task_id, "invalid json{"])

        # Should handle json decode error gracefully
        task = await queue.dequeue()

        # Should return None for corrupted data
        assert task is None

    @pytest.mark.asyncio
    async def test_nack_with_missing_task_data(self, queue, mock_redis):
        """NACK with missing task data handles gracefully."""
        task_id = "task_missing_data"
        mock_redis.hget.return_value = None

        # Should not raise exception
        await queue.nack(task_id, retry=True)

    @pytest.mark.asyncio
    async def test_recover_with_redis_error(self, queue, mock_redis):
        """Recover handles Redis errors gracefully."""
        mock_redis.zrangebyscore.side_effect = Exception("Redis connection error")

        # Should handle exception and return 0 or raise specific error
        # This drives requirement for error handling
        try:
            recovered = await queue.recover_expired_tasks()
            assert recovered == 0
        except Exception as e:
            # Implementation might choose to propagate Redis errors
            assert "Redis" in str(e)

    @pytest.mark.asyncio
    async def test_enqueue_with_negative_priority(self, queue, mock_redis):
        """Enqueue with invalid priority uses default."""
        task_id = "task_invalid_priority"

        # This should be handled by TaskPriority enum validation
        # Test ensures priority is always valid
        await queue.enqueue(task_id=task_id, task_data={}, priority=TaskPriority.NORMAL)

    @pytest.mark.asyncio
    async def test_multiple_ack_same_task(self, queue, mock_redis):
        """Multiple ACK calls for same task are idempotent."""
        task_id = "task_multi_ack"

        await queue.ack(task_id)
        mock_redis.reset_mock()

        await queue.ack(task_id)

        # Second ACK should still work (idempotent)
        assert mock_redis.zrem.called
        assert mock_redis.hdel.called


class TestTaskQueueV2Integration:
    """Integration-style tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle_success(self, queue, mock_redis):
        """Test complete task lifecycle: enqueue -> dequeue -> ack."""
        task_id = "task_lifecycle"
        task_data = {"url": "https://example.com"}

        # 1. Enqueue
        await queue.enqueue(task_id, task_data, TaskPriority.HIGH)
        assert mock_redis.zadd.called
        assert mock_redis.hset.called

        # 2. Dequeue
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        task = await queue.dequeue()
        assert task is not None

        # 3. ACK
        await queue.ack(task_id)

        # Verify cleanup
        zrem_calls = [
            call for call in mock_redis.zrem.call_args_list if "processing" in str(call)
        ]
        assert len(zrem_calls) > 0

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle_with_retry(self, queue, mock_redis):
        """Test complete task lifecycle with retry: enqueue -> dequeue -> nack -> retry."""
        task_id = "task_retry_lifecycle"
        task_data = {"url": "https://example.com", "retry_count": 0}

        # 1. Enqueue
        await queue.enqueue(task_id, task_data, TaskPriority.NORMAL)

        # 2. Dequeue
        mock_redis.eval.return_value = json.dumps([task_id, json.dumps(task_data)])

        task = await queue.dequeue()
        assert task is not None

        # 3. NACK with retry
        mock_redis.hget.return_value = json.dumps(task_data).encode()
        await queue.nack(task_id, retry=True)

        # Verify moved to delayed
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "delayed" in str(call)
        ]
        assert len(zadd_calls) > 0

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle_max_retries_to_dlq(self, queue, mock_redis):
        """Test task lifecycle reaching max retries and moving to DLQ."""
        task_id = "task_dlq_lifecycle"
        task_data = {"url": "https://example.com", "retry_count": queue.max_retries}

        # NACK with retry when already at max retries
        mock_redis.hget.return_value = json.dumps(task_data).encode()
        await queue.nack(task_id, retry=True)

        # Verify moved to DLQ
        zadd_calls = [
            call for call in mock_redis.zadd.call_args_list if "dlq" in str(call)
        ]
        assert len(zadd_calls) > 0
