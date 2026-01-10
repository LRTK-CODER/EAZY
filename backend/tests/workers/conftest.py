"""
Worker test fixtures
Phase 3: Architecture Improvement - TDD
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from redis.asyncio import Redis

from app.core.config import settings
from app.core.queue import TaskManager
from app.core.dlq import DLQManager
from app.core.recovery import OrphanRecovery


@pytest.fixture
async def redis_client() -> Redis:
    """Test Redis client with single connection to avoid timing issues.

    Using single_connection_client=True ensures all Redis operations use the
    same connection, preventing race conditions.
    """
    redis = Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        single_connection_client=True
    )
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_worker_queues(redis_client: Redis):
    """Clean all worker-related queues before and after tests"""
    keys = [
        "eazy_task_queue",
        "eazy_task_queue:processing",
        "eazy_task_queue:dlq",
    ]
    for key in keys:
        await redis_client.delete(key)

    # Clean heartbeats and metadata
    for pattern in ["eazy:heartbeat:*", "eazy:dlq:meta:*"]:
        cursor = 0
        while True:
            cursor, found_keys = await redis_client.scan(cursor, match=pattern)
            if found_keys:
                await redis_client.delete(*found_keys)
            if cursor == 0:
                break

    yield

    # Cleanup after test
    for key in keys:
        await redis_client.delete(key)


@pytest.fixture
def mock_task_manager(redis_client: Redis) -> TaskManager:
    """Create TaskManager for testing"""
    return TaskManager(redis_client)


@pytest.fixture
def mock_dlq_manager(redis_client: Redis) -> DLQManager:
    """Create DLQManager for testing"""
    return DLQManager(redis_client)


@pytest.fixture
def mock_orphan_recovery(redis_client: Redis) -> OrphanRecovery:
    """Create OrphanRecovery for testing"""
    return OrphanRecovery(redis_client)


@pytest.fixture
def mock_crawler_service():
    """Mock CrawlerService for testing"""
    mock = MagicMock()
    mock.crawl = AsyncMock(return_value=(
        ["http://example.com/page1", "http://example.com/page2"],
        {
            "http://example.com/page1": {
                "request": {"method": "GET", "headers": {}},
                "response": {"status": 200, "headers": {}},
                "parameters": {}
            },
            "http://example.com/page2": {
                "request": {"method": "GET", "headers": {}},
                "response": {"status": 200, "headers": {}},
                "parameters": {}
            }
        }
    ))
    return mock
