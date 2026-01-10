"""
Phase 4.5 Day 3: Priority Queue - Aging/Starvation Prevention Tests
TDD RED Phase - These tests should FAIL before implementation

Tests:
1. Timestamp tests (enqueued_at field)
2. AgingConfig tests
3. Promotion mechanism tests
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
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


class TestTaskPayloadTimestamp:
    """Task payload should include enqueued_at timestamp."""

    @pytest.mark.asyncio
    async def test_enqueue_adds_enqueued_at(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Task payload should include enqueued_at ISO timestamp."""
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )

        task_json = await redis_client.lindex("eazy_task_queue:low", 0)
        task_data = json.loads(task_json)

        assert "enqueued_at" in task_data
        # Should be valid ISO format
        enqueued_at = datetime.fromisoformat(task_data["enqueued_at"])
        assert enqueued_at is not None
        # Should be recent (within last minute)
        now = datetime.now(timezone.utc)
        assert (now - enqueued_at).total_seconds() < 60


class TestAgingConfiguration:
    """AgingConfig configuration tests."""

    def test_aging_config_exists(self):
        """AgingConfig should exist with threshold settings."""
        from app.core.priority import AgingConfig

        config = AgingConfig()
        assert hasattr(config, "low_to_normal_seconds")
        assert hasattr(config, "normal_to_high_seconds")
        assert hasattr(config, "high_to_critical_seconds")

    def test_default_aging_thresholds(self):
        """Default aging thresholds should be reasonable."""
        from app.core.priority import AgingConfig

        config = AgingConfig()
        # LOW -> NORMAL should be shortest
        assert config.low_to_normal_seconds > 0
        # NORMAL -> HIGH should be longer
        assert config.normal_to_high_seconds > config.low_to_normal_seconds
        # HIGH -> CRITICAL should be longest
        assert config.high_to_critical_seconds > config.normal_to_high_seconds

    def test_custom_aging_thresholds(self):
        """AgingConfig should accept custom thresholds."""
        from app.core.priority import AgingConfig

        config = AgingConfig(
            low_to_normal_seconds=60,
            normal_to_high_seconds=120,
            high_to_critical_seconds=180,
        )
        assert config.low_to_normal_seconds == 60
        assert config.normal_to_high_seconds == 120
        assert config.high_to_critical_seconds == 180


class TestAgingMechanism:
    """Aging mechanism tests."""

    @pytest.mark.asyncio
    async def test_promote_aged_low_to_normal(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """LOW priority task aged beyond threshold should promote to NORMAL."""
        from app.core.priority import AgingConfig

        # Create aged task (fake old timestamp - 10 minutes ago)
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        old_task = {
            "id": "aged-task-1",
            "db_task_id": 100,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.LOW.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue:low", json.dumps(old_task))

        # Run aging check with 1 minute threshold
        promoted = await task_manager.promote_aged_tasks(
            config=AgingConfig(low_to_normal_seconds=60)
        )

        assert promoted >= 1

        # Task should be in normal queue now
        normal_len = await redis_client.llen("eazy_task_queue")
        low_len = await redis_client.llen("eazy_task_queue:low")

        assert normal_len == 1
        assert low_len == 0

    @pytest.mark.asyncio
    async def test_promote_updates_priority_in_payload(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Promoted task should have updated priority in payload."""
        from app.core.priority import AgingConfig

        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        old_task = {
            "id": "aged-task-2",
            "db_task_id": 200,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.LOW.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue:low", json.dumps(old_task))

        await task_manager.promote_aged_tasks(
            config=AgingConfig(low_to_normal_seconds=60)
        )

        task_json = await redis_client.lindex("eazy_task_queue", 0)
        task_data = json.loads(task_json)

        # Priority should be updated to NORMAL
        assert task_data["priority"] == TaskPriority.NORMAL.value
        # Should preserve original_priority
        assert task_data.get("original_priority") == TaskPriority.LOW.value

    @pytest.mark.asyncio
    async def test_no_promotion_for_fresh_tasks(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Fresh tasks should not be promoted."""
        from app.core.priority import AgingConfig

        # Enqueue a fresh task
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.LOW,
        )

        # Run aging with 1 hour threshold (task is fresh, won't be promoted)
        promoted = await task_manager.promote_aged_tasks(
            config=AgingConfig(low_to_normal_seconds=3600)
        )

        assert promoted == 0

        # Task should still be in LOW queue
        low_len = await redis_client.llen("eazy_task_queue:low")
        assert low_len == 1

    @pytest.mark.asyncio
    async def test_cascading_promotion_normal_to_high(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Aged NORMAL task should promote to HIGH."""
        from app.core.priority import AgingConfig

        old_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        old_task = {
            "id": "aged-task-3",
            "db_task_id": 300,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.NORMAL.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue", json.dumps(old_task))

        await task_manager.promote_aged_tasks(
            config=AgingConfig(normal_to_high_seconds=60)
        )

        high_len = await redis_client.llen("eazy_task_queue:high")
        normal_len = await redis_client.llen("eazy_task_queue")

        assert high_len == 1
        assert normal_len == 0

    @pytest.mark.asyncio
    async def test_cascading_promotion_high_to_critical(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """Aged HIGH task should promote to CRITICAL."""
        from app.core.priority import AgingConfig

        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        old_task = {
            "id": "aged-task-4",
            "db_task_id": 400,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.HIGH.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue:high", json.dumps(old_task))

        await task_manager.promote_aged_tasks(
            config=AgingConfig(high_to_critical_seconds=60)
        )

        critical_len = await redis_client.llen("eazy_task_queue:critical")
        high_len = await redis_client.llen("eazy_task_queue:high")

        assert critical_len == 1
        assert high_len == 0

    @pytest.mark.asyncio
    async def test_critical_tasks_not_promoted(
        self, task_manager: TaskManager, redis_client: Redis, clean_priority_queues
    ):
        """CRITICAL tasks should not be promoted (already highest)."""
        from app.core.priority import AgingConfig

        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        old_task = {
            "id": "critical-task",
            "db_task_id": 500,
            "type": "crawl",
            "project_id": 1,
            "target_id": 1,
            "priority": TaskPriority.CRITICAL.value,
            "enqueued_at": old_time,
            "timestamp": old_time,
        }
        await redis_client.rpush("eazy_task_queue:critical", json.dumps(old_task))

        promoted = await task_manager.promote_aged_tasks(config=AgingConfig())

        assert promoted == 0

        # Task should still be in CRITICAL queue
        critical_len = await redis_client.llen("eazy_task_queue:critical")
        assert critical_len == 1
