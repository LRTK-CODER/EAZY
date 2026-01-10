"""
Phase 4.5 Day 2: Priority Queue - Dequeue Tests
TDD RED Phase - These tests should FAIL before implementation

Tests:
1. Priority ordering tests (CRITICAL > HIGH > NORMAL > LOW)
2. FIFO within same priority
3. Processing queue integration
"""

import json
import pytest
from redis.asyncio import Redis

from app.core.queue import TaskManager
from app.core.priority import TaskPriority


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


class TestPriorityDequeue:
    """Priority-ordered dequeue tests."""

    @pytest.mark.asyncio
    async def test_dequeue_critical_before_high(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """CRITICAL tasks should be dequeued before HIGH."""
        # Enqueue HIGH first, then CRITICAL
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=2,
            db_task_id=200,
            priority=TaskPriority.CRITICAL,
        )

        # First dequeue should be CRITICAL
        result = await task_manager.dequeue_task(timeout=1)
        assert result is not None
        task_data, _ = result
        assert task_data["db_task_id"] == 200
        assert task_data["priority"] == TaskPriority.CRITICAL.value

    @pytest.mark.asyncio
    async def test_dequeue_high_before_normal(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """HIGH tasks should be dequeued before NORMAL."""
        # Enqueue NORMAL first, then HIGH
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.NORMAL,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=2,
            db_task_id=200,
            priority=TaskPriority.HIGH,
        )

        result = await task_manager.dequeue_task(timeout=1)
        task_data, _ = result
        assert task_data["db_task_id"] == 200

    @pytest.mark.asyncio
    async def test_dequeue_normal_before_low(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """NORMAL tasks should be dequeued before LOW."""
        # Enqueue LOW first, then NORMAL
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=2,
            db_task_id=200,
            priority=TaskPriority.NORMAL,
        )

        result = await task_manager.dequeue_task(timeout=1)
        task_data, _ = result
        assert task_data["db_task_id"] == 200

    @pytest.mark.asyncio
    async def test_dequeue_fifo_within_same_priority(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Tasks with same priority should be FIFO (First In, First Out)."""
        # Enqueue three HIGH priority tasks
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=2,
            db_task_id=200,
            priority=TaskPriority.HIGH,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=3,
            db_task_id=300,
            priority=TaskPriority.HIGH,
        )

        # Should come out in order: 100, 200, 300
        r1 = await task_manager.dequeue_task(timeout=1)
        r2 = await task_manager.dequeue_task(timeout=1)
        r3 = await task_manager.dequeue_task(timeout=1)

        assert r1[0]["db_task_id"] == 100
        assert r2[0]["db_task_id"] == 200
        assert r3[0]["db_task_id"] == 300

    @pytest.mark.asyncio
    async def test_dequeue_moves_to_processing_queue(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Dequeued task should be in shared processing queue."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.CRITICAL,
        )

        await task_manager.dequeue_task(timeout=1)

        # Processing queue should have 1 task
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 1

        # Critical queue should be empty
        critical_len = await redis_client.llen("eazy_task_queue:critical")
        assert critical_len == 0

    @pytest.mark.asyncio
    async def test_dequeue_full_priority_order(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Complete priority order test: CRITICAL -> HIGH -> NORMAL -> LOW."""
        # Enqueue in reverse order (LOW first)
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=2,
            db_task_id=200,
            priority=TaskPriority.NORMAL,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=3,
            db_task_id=300,
            priority=TaskPriority.HIGH,
        )
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=4,
            db_task_id=400,
            priority=TaskPriority.CRITICAL,
        )

        # Dequeue order should be: 400 (CRITICAL), 300 (HIGH), 200 (NORMAL), 100 (LOW)
        results = []
        for _ in range(4):
            r = await task_manager.dequeue_task(timeout=1)
            results.append(r[0]["db_task_id"])

        assert results == [400, 300, 200, 100]

    @pytest.mark.asyncio
    async def test_dequeue_empty_returns_none(
        self, task_manager: TaskManager, clean_priority_queues
    ):
        """Empty queues should return None after timeout."""
        result = await task_manager.dequeue_task(timeout=1)
        assert result is None
