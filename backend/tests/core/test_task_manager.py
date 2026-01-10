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
async def test_dequeue_task_blmove():
    """Test dequeuing a task using BLMOVE (BRPOPLPUSH replacement)."""
    mock_redis = AsyncMock()
    # BLMOVE returns the moved value as string
    task_json = '{"id": "123", "type": "crawl", "target_id": 1}'
    mock_redis.blmove.return_value = task_json

    task_manager = TaskManager(redis=mock_redis)
    result = await task_manager.dequeue_task(timeout=5)

    assert result is not None
    task_data, returned_json = result
    assert task_data["id"] == "123"
    assert task_data["type"] == "crawl"
    assert returned_json == task_json
    mock_redis.blmove.assert_called_once_with(
        "eazy_task_queue",
        "eazy_task_queue:processing",
        5,
        "RIGHT",
        "LEFT",
    )


@pytest.mark.asyncio
async def test_dequeue_task_empty_queue():
    """Test dequeue returns None when queue is empty after timeout."""
    mock_redis = AsyncMock()
    mock_redis.blmove.return_value = None

    task_manager = TaskManager(redis=mock_redis)
    result = await task_manager.dequeue_task(timeout=1)

    assert result is None
    mock_redis.blmove.assert_called_once_with(
        "eazy_task_queue",
        "eazy_task_queue:processing",
        1,
        "RIGHT",
        "LEFT",
    )
