"""
Phase 4.5 Day 1: Priority Queue - Enqueue Tests
TDD RED Phase - These tests should FAIL before implementation

Tests:
1. TaskPriority enum tests (4 tests)
2. Priority-based enqueue tests (5 tests)
"""

import json

import pytest
from redis.asyncio import Redis

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


class TestTaskPriority:
    """TaskPriority enum tests."""

    def test_priority_enum_exists(self):
        """TaskPriority IntEnum should exist in priority module."""
        from app.core.priority import TaskPriority

        assert TaskPriority is not None

    def test_priority_has_four_levels(self):
        """TaskPriority should have LOW, NORMAL, HIGH, CRITICAL levels."""
        from app.core.priority import TaskPriority

        assert hasattr(TaskPriority, "LOW")
        assert hasattr(TaskPriority, "NORMAL")
        assert hasattr(TaskPriority, "HIGH")
        assert hasattr(TaskPriority, "CRITICAL")

    def test_priority_values_are_ordered(self):
        """Priority values should be ordered: LOW < NORMAL < HIGH < CRITICAL."""
        from app.core.priority import TaskPriority

        assert TaskPriority.LOW < TaskPriority.NORMAL
        assert TaskPriority.NORMAL < TaskPriority.HIGH
        assert TaskPriority.HIGH < TaskPriority.CRITICAL

    def test_priority_integer_values(self):
        """Priority should have integer values 0, 1, 2, 3."""
        from app.core.priority import TaskPriority

        assert TaskPriority.LOW == 0
        assert TaskPriority.NORMAL == 1
        assert TaskPriority.HIGH == 2
        assert TaskPriority.CRITICAL == 3


class TestPriorityEnqueue:
    """Priority-based enqueue tests."""

    @pytest.mark.asyncio
    async def test_enqueue_with_default_priority(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Default enqueue should use NORMAL priority (backward compatible).

        Task should be placed in the default queue 'eazy_task_queue'.
        """
        await task_manager.enqueue_crawl_task(project_id=1, target_id=1, db_task_id=100)

        # Should be in normal queue (default key for backward compatibility)
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 1

    @pytest.mark.asyncio
    async def test_enqueue_with_critical_priority(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """CRITICAL priority should go to critical queue."""
        from app.core.priority import TaskPriority

        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.CRITICAL,
        )

        critical_len = await redis_client.llen("eazy_task_queue:critical")
        normal_len = await redis_client.llen("eazy_task_queue")

        assert critical_len == 1
        assert normal_len == 0

    @pytest.mark.asyncio
    async def test_enqueue_with_high_priority(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """HIGH priority should go to high queue."""
        from app.core.priority import TaskPriority

        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )

        high_len = await redis_client.llen("eazy_task_queue:high")
        assert high_len == 1

    @pytest.mark.asyncio
    async def test_enqueue_with_low_priority(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """LOW priority should go to low queue."""
        from app.core.priority import TaskPriority

        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )

        low_len = await redis_client.llen("eazy_task_queue:low")
        assert low_len == 1

    @pytest.mark.asyncio
    async def test_enqueue_stores_priority_in_payload(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Task payload should include priority field."""
        from app.core.priority import TaskPriority

        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH,
        )

        task_json = await redis_client.lindex("eazy_task_queue:high", 0)
        task_data = json.loads(task_json)

        assert "priority" in task_data
        assert task_data["priority"] == TaskPriority.HIGH.value

        # Should also include enqueued_at for aging mechanism
        assert "enqueued_at" in task_data
