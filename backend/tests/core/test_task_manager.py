import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.queue import TaskManager

@pytest.mark.asyncio
async def test_enqueue_task(client):
    """Test enqueuing a crawl task."""
    mock_redis = AsyncMock()
    task_manager = TaskManager(redis=mock_redis)

    project_id = 1
    target_id = 1
    db_task_id = 123  # DB에 생성된 Task ID

    task_id = await task_manager.enqueue_crawl_task(project_id, target_id, db_task_id)

    assert task_id is not None
    # Verify Redis rpush was called to add to queue
    mock_redis.rpush.assert_called_once()
    
@pytest.mark.asyncio
async def test_dequeue_task_blpop():
    """Test dequeuing a task using BLPOP."""
    mock_redis = AsyncMock()
    # BLPOP returns (key, value) tuple
    mock_redis.blpop.return_value = (
        "eazy_task_queue",
        '{"id": "123", "type": "crawl", "target_id": 1}'
    )

    task_manager = TaskManager(redis=mock_redis)
    task = await task_manager.dequeue_task(timeout=5)

    assert task is not None
    assert task["id"] == "123"
    assert task["type"] == "crawl"
    mock_redis.blpop.assert_called_once_with("eazy_task_queue", timeout=5)


@pytest.mark.asyncio
async def test_dequeue_task_empty_queue():
    """Test dequeue returns None when queue is empty after timeout."""
    mock_redis = AsyncMock()
    mock_redis.blpop.return_value = None

    task_manager = TaskManager(redis=mock_redis)
    task = await task_manager.dequeue_task(timeout=1)

    assert task is None
    mock_redis.blpop.assert_called_once_with("eazy_task_queue", timeout=1)
