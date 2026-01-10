"""
Phase 4.5 Day 5: Priority Queue - End-to-End Integration Tests
TDD RED Phase - These tests verify full system integration

Tests:
1. Backward compatibility with existing enqueue/dequeue
2. Worker processes priorities correctly
3. Aging integration during idle
4. Queue stats API
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
from redis.asyncio import Redis

from app.core.queue import TaskManager
from app.core.priority import TaskPriority, AgingConfig


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


class TestBackwardCompatibility:
    """Tests ensuring existing code continues to work."""

    @pytest.mark.asyncio
    async def test_existing_enqueue_still_works(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Enqueue without priority should use NORMAL (backward compatible)."""
        # Old-style enqueue without priority parameter
        task_id = await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
        )

        assert task_id is not None

        # Should be in NORMAL queue (default)
        normal_len = await redis_client.llen("eazy_task_queue")
        assert normal_len == 1

        # Check payload has priority field
        task_json = await redis_client.lindex("eazy_task_queue", 0)
        task_data = json.loads(task_json)
        assert task_data["priority"] == TaskPriority.NORMAL.value

    @pytest.mark.asyncio
    async def test_existing_dequeue_still_works(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Dequeue should work with existing NORMAL priority tasks."""
        # Enqueue without priority (uses NORMAL)
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
        )

        # Dequeue should work
        result = await task_manager.dequeue_task(timeout=1)
        assert result is not None

        task_data, task_json = result
        assert task_data["db_task_id"] == 100
        assert task_data["priority"] == TaskPriority.NORMAL.value


class TestWorkerPriorityProcessing:
    """Tests simulating worker processing behavior."""

    @pytest.mark.asyncio
    async def test_worker_processes_critical_first(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Worker should always process CRITICAL tasks before others."""
        # Enqueue tasks in reverse priority order
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100, priority=TaskPriority.LOW
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=200, priority=TaskPriority.NORMAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=3, db_task_id=300, priority=TaskPriority.CRITICAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=4, db_task_id=400, priority=TaskPriority.HIGH
        )

        # Simulate worker loop - dequeue, ack, repeat
        processed = []
        for _ in range(4):
            result = await task_manager.dequeue_task(timeout=1)
            if result:
                task_data, task_json = result
                processed.append(task_data["db_task_id"])
                await task_manager.ack_task(task_json)

        # Order should be: CRITICAL(300), HIGH(400), NORMAL(200), LOW(100)
        assert processed == [300, 400, 200, 100]

    @pytest.mark.asyncio
    async def test_worker_handles_mixed_arrivals(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Worker should handle tasks arriving in any order."""
        # First batch: LOW tasks
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100, priority=TaskPriority.LOW
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=101, priority=TaskPriority.LOW
        )

        # Dequeue one LOW task
        result = await task_manager.dequeue_task(timeout=1)
        task_data, task_json = result
        assert task_data["priority"] == TaskPriority.LOW.value
        await task_manager.ack_task(task_json)

        # New CRITICAL arrives
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=3, db_task_id=200, priority=TaskPriority.CRITICAL
        )

        # Next dequeue should be CRITICAL (not remaining LOW)
        result = await task_manager.dequeue_task(timeout=1)
        task_data, task_json = result
        assert task_data["db_task_id"] == 200
        assert task_data["priority"] == TaskPriority.CRITICAL.value


class TestAgingIntegration:
    """Tests for aging mechanism integration."""

    @pytest.mark.asyncio
    async def test_aging_promotes_during_idle(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Aged tasks should be promoted when promote_aged_tasks is called."""
        # Create an old task directly (simulating 10 min old)
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        old_task = {
            "id": "old-task-1",
            "db_task_id": 100,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.LOW.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue:low", json.dumps(old_task))

        # Initial state
        lengths_before = await task_manager.get_all_queue_lengths()
        assert lengths_before["low"] == 1
        assert lengths_before["normal"] == 0

        # Run aging with 1 minute threshold
        promoted = await task_manager.promote_aged_tasks(
            config=AgingConfig(low_to_normal_seconds=60)
        )

        assert promoted == 1

        # Final state
        lengths_after = await task_manager.get_all_queue_lengths()
        assert lengths_after["low"] == 0
        assert lengths_after["normal"] == 1


class TestQueueStatsAPI:
    """Tests for queue statistics functionality."""

    @pytest.mark.asyncio
    async def test_queue_stats_api(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Queue stats should reflect current state accurately."""
        # Empty state
        lengths = await task_manager.get_all_queue_lengths()
        assert all(v == 0 for v in lengths.values())

        # Add tasks
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100, priority=TaskPriority.CRITICAL
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=101, priority=TaskPriority.HIGH
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=3, db_task_id=102, priority=TaskPriority.HIGH
        )

        lengths = await task_manager.get_all_queue_lengths()
        assert lengths["critical"] == 1
        assert lengths["high"] == 2

        # Process one
        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result

        lengths = await task_manager.get_all_queue_lengths()
        assert lengths["critical"] == 0
        assert lengths["processing"] == 1

        # ACK it
        await task_manager.ack_task(task_json)

        lengths = await task_manager.get_all_queue_lengths()
        assert lengths["processing"] == 0

    @pytest.mark.asyncio
    async def test_queue_stats_with_dlq(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """DLQ should be tracked in queue stats."""
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100, priority=TaskPriority.HIGH
        )

        # Dequeue and NACK to DLQ
        result = await task_manager.dequeue_task(timeout=1)
        _, task_json = result
        await task_manager.nack_task(task_json, retry=False)

        lengths = await task_manager.get_all_queue_lengths()
        assert lengths["high"] == 0
        assert lengths["dlq"] == 1
