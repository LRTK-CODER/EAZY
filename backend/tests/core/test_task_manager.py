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
async def test_dequeue_task():
    """Test dequeuing a task."""
    mock_redis = AsyncMock()
    # Mock lpop to return a sample task JSON
    mock_redis.lpop.return_value = '{"id": "123", "type": "crawl", "target_id": 1}'
    
    task_manager = TaskManager(redis=mock_redis)
    task = await task_manager.dequeue_task()
    
    assert task is not None
    assert task["id"] == "123"
    assert task["type"] == "crawl"
