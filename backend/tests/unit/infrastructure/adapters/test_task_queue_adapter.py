"""TaskQueueAdapter 테스트."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.adapters.task_queue_adapter import TaskQueueAdapter


class MockTask:
    """테스트용 Task Mock."""

    def __init__(self, id: int):
        self.id = id


@pytest.mark.asyncio
async def test_enqueue_adds_url_to_pending():
    """enqueue가 URL을 pending 목록에 추가하는지 테스트."""
    mock_manager = MagicMock()
    adapter = TaskQueueAdapter(mock_manager)

    task_data = {
        "crawl_url": "http://example.com",
        "target_id": 1,
        "project_id": 1,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 1,
    }
    await adapter.enqueue(task_data)

    assert adapter.get_pending_count() == 1


@pytest.mark.asyncio
async def test_enqueue_multiple_urls():
    """여러 URL을 추가할 수 있는지 테스트."""
    mock_manager = MagicMock()
    adapter = TaskQueueAdapter(mock_manager)

    task_data_1 = {
        "crawl_url": "http://example.com/1",
        "target_id": 1,
        "project_id": 1,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 1,
    }
    task_data_2 = {
        "crawl_url": "http://example.com/2",
        "target_id": 1,
        "project_id": 1,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 1,
    }

    await adapter.enqueue(task_data_1)
    await adapter.enqueue(task_data_2)

    assert adapter.get_pending_count() == 2


@pytest.mark.asyncio
async def test_flush_calls_spawn_child_tasks_once():
    """flush가 spawn_child_tasks를 한 번만 호출하는지 테스트."""
    mock_manager = MagicMock()
    mock_manager.spawn_child_tasks = AsyncMock(
        return_value=[MockTask(100), MockTask(101)]
    )
    adapter = TaskQueueAdapter(mock_manager)

    task_data_1 = {
        "crawl_url": "http://example.com/1",
        "target_id": 1,
        "project_id": 2,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 10,
    }
    task_data_2 = {
        "crawl_url": "http://example.com/2",
        "target_id": 1,
        "project_id": 2,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 10,
    }

    await adapter.enqueue(task_data_1)
    await adapter.enqueue(task_data_2)

    count = await adapter.flush()

    assert count == 2
    mock_manager.spawn_child_tasks.assert_called_once()

    # Verify parameters
    call_kwargs = mock_manager.spawn_child_tasks.call_args[1]
    assert call_kwargs["parent_task_id"] == 10
    assert call_kwargs["target_id"] == 1
    assert call_kwargs["project_id"] == 2
    assert call_kwargs["discovered_urls"] == [
        "http://example.com/1",
        "http://example.com/2",
    ]


@pytest.mark.asyncio
async def test_flush_clears_pending():
    """flush 후 pending 목록이 비워지는지 테스트."""
    mock_manager = MagicMock()
    mock_manager.spawn_child_tasks = AsyncMock(return_value=[MockTask(100)])
    adapter = TaskQueueAdapter(mock_manager)

    task_data = {
        "crawl_url": "http://example.com",
        "target_id": 1,
        "project_id": 1,
        "depth": 1,
        "max_depth": 3,
        "parent_task_id": 1,
    }

    await adapter.enqueue(task_data)
    await adapter.flush()

    assert adapter.get_pending_count() == 0


@pytest.mark.asyncio
async def test_flush_returns_zero_when_empty():
    """비어있을 때 flush가 0을 반환하는지 테스트."""
    mock_manager = MagicMock()
    adapter = TaskQueueAdapter(mock_manager)

    count = await adapter.flush()

    assert count == 0
    mock_manager.spawn_child_tasks.assert_not_called()


@pytest.mark.asyncio
async def test_get_pending_count_initially_zero():
    """초기 pending 카운트가 0인지 테스트."""
    mock_manager = MagicMock()
    adapter = TaskQueueAdapter(mock_manager)

    assert adapter.get_pending_count() == 0
