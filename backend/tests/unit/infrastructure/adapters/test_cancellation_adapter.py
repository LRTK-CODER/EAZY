"""CancellationAdapter 테스트."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.adapters.cancellation_adapter import CancellationAdapter


@pytest.mark.asyncio
async def test_is_cancelled_returns_true_when_flag_exists():
    """cancel 플래그가 있으면 True를 반환하는지 테스트."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value="1")

    adapter = CancellationAdapter(mock_redis)
    result = await adapter.is_cancelled(task_id=100)

    assert result is True
    mock_redis.get.assert_called_once_with("task:100:cancel")


@pytest.mark.asyncio
async def test_is_cancelled_returns_false_when_flag_not_exists():
    """cancel 플래그가 없으면 False를 반환하는지 테스트."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)

    adapter = CancellationAdapter(mock_redis)
    result = await adapter.is_cancelled(task_id=100)

    assert result is False
    mock_redis.get.assert_called_once_with("task:100:cancel")


@pytest.mark.asyncio
async def test_is_cancelled_with_different_task_ids():
    """다른 task_id로 올바른 키를 사용하는지 테스트."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)

    adapter = CancellationAdapter(mock_redis)

    await adapter.is_cancelled(task_id=1)
    mock_redis.get.assert_called_with("task:1:cancel")

    await adapter.is_cancelled(task_id=999)
    mock_redis.get.assert_called_with("task:999:cancel")
