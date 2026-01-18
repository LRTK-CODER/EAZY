"""
Phase 4.5 Day 4: Priority Queue - NACK Priority Preservation Tests
TDD RED Phase - These tests should FAIL before implementation

Tests:
1. NACK returns task to original priority queue
2. retry_count increments on NACK
3. DLQ preserves priority info
4. Get all queue lengths
"""

import json

import pytest
from redis.asyncio import Redis

from app.core.priority import TaskPriority
from app.core.queue import TaskManager


@pytest.fixture
async def redis_client() -> Redis:
    """Test Redis client with single connection for test isolation."""
    redis = Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
        single_connection_client=True,
    )
    # Initialize connection (required for single_connection_client in redis-py 7.x)
    await redis.ping()
    yield redis
    await redis.aclose()


@pytest.fixture
async def task_manager(redis_client: Redis) -> TaskManager:
    """Test TaskManager instance."""
    return TaskManager(redis_client)


@pytest.fixture
async def clean_priority_queues(redis_client: Redis):
    """Clean all priority queues before/after tests."""
    keys = [
        "eazy_task_queue",
        "eazy_task_queue:critical",
        "eazy_task_queue:high",
        "eazy_task_queue:low",
        "eazy_task_queue:processing",
        "eazy_task_queue:dlq",
    ]
    for key in keys:
        await redis_client.delete(key)
    yield
    for key in keys:
        await redis_client.delete(key)


class TestNackPriorityPreservation:
    """NACK should preserve task priority when returning to queue."""

    @pytest.mark.asyncio
    async def test_nack_returns_to_same_priority_queue(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """NACK should return task to its original priority queue."""
        # Enqueue HIGH priority task
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )

        # Dequeue it (moves to processing)
        result = await task_manager.dequeue_task(timeout=1)
        task_data, task_json = result

        # NACK with retry
        await task_manager.nack_task(task_json, retry=True)

        # Task should be back in HIGH queue, not default queue
        high_len = await redis_client.llen("eazy_task_queue:high")
        normal_len = await redis_client.llen("eazy_task_queue")

        assert high_len == 1
        assert normal_len == 0

    @pytest.mark.asyncio
    async def test_nack_critical_returns_to_critical(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """CRITICAL task should return to CRITICAL queue on NACK."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.CRITICAL,
        )

        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result

        await task_manager.nack_task(task_json, retry=True)

        critical_len = await redis_client.llen("eazy_task_queue:critical")
        assert critical_len == 1

    @pytest.mark.asyncio
    async def test_nack_low_returns_to_low(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """LOW task should return to LOW queue on NACK."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )

        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result

        await task_manager.nack_task(task_json, retry=True)

        low_len = await redis_client.llen("eazy_task_queue:low")
        assert low_len == 1

    @pytest.mark.asyncio
    async def test_nack_increments_retry_count(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """NACK with retry should increment retry_count in payload."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )

        # First dequeue and NACK
        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result
        await task_manager.nack_task(task_json, retry=True)

        # Check retry_count
        task_json_after = await redis_client.lindex("eazy_task_queue:high", 0)
        task_data = json.loads(task_json_after)
        assert task_data.get("retry_count", 0) == 1

        # Second dequeue and NACK
        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result
        await task_manager.nack_task(task_json, retry=True)

        # Check retry_count again
        task_json_after = await redis_client.lindex("eazy_task_queue:high", 0)
        task_data = json.loads(task_json_after)
        assert task_data.get("retry_count", 0) == 2

    @pytest.mark.asyncio
    async def test_nack_dlq_preserves_priority_info(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """DLQ should preserve original priority information."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.CRITICAL,
        )

        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result

        # NACK without retry (move to DLQ)
        await task_manager.nack_task(task_json, retry=False)

        # Check DLQ has the task with priority info
        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 1

        dlq_task_json = await redis_client.lindex("eazy_task_queue:dlq", 0)
        dlq_task = json.loads(dlq_task_json)
        assert dlq_task["priority"] == TaskPriority.CRITICAL.value


class TestQueueLengthQueries:
    """Queue length query tests."""

    @pytest.mark.asyncio
    async def test_get_all_queue_lengths(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Should return lengths for all priority queues."""
        # Enqueue tasks at different priorities
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100, priority=TaskPriority.CRITICAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=101, priority=TaskPriority.CRITICAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=3, db_task_id=102, priority=TaskPriority.HIGH
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=4, db_task_id=103, priority=TaskPriority.NORMAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=5, db_task_id=104, priority=TaskPriority.LOW
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=6, db_task_id=105, priority=TaskPriority.LOW
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=7, db_task_id=106, priority=TaskPriority.LOW
        )

        lengths = await task_manager.get_all_queue_lengths()

        assert lengths["critical"] == 2
        assert lengths["high"] == 1
        assert lengths["normal"] == 1
        assert lengths["low"] == 3
        assert lengths["processing"] == 0
        assert lengths["dlq"] == 0
