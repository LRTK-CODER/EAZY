import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_asset_service_context_manager():
    """AssetService supports async context manager."""
    mock_session = AsyncMock()

    from app.services.asset_service import AssetService

    async with AssetService(mock_session) as service:
        assert service is not None
        assert service.session == mock_session


@pytest.mark.asyncio
async def test_asset_service_buffers_until_batch_size():
    """Assets are buffered until BATCH_SIZE is reached."""
    mock_session = AsyncMock()
    # Mock exec to return no existing asset
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    from app.services.asset_service import AssetService

    async with AssetService(mock_session) as service:
        # Add 49 assets (below BATCH_SIZE of 50)
        for i in range(49):
            await service.process_asset(
                target_id=1, task_id=1, url=f"http://test{i}.com"
            )

        # Should NOT have committed yet (buffering)
        assert mock_session.commit.call_count == 0
        assert len(service._pending_assets) == 49


@pytest.mark.asyncio
async def test_asset_service_flush_commits_batch():
    """flush() commits all pending assets when BATCH_SIZE is reached."""
    mock_session = AsyncMock()
    # Mock exec to return no existing asset
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    from app.services.asset_service import AssetService

    async with AssetService(mock_session) as service:
        # Add exactly BATCH_SIZE (50) assets
        for i in range(50):
            await service.process_asset(
                target_id=1, task_id=1, url=f"http://test{i}.com"
            )

        # Should have committed once (at 50th asset triggering flush)
        assert mock_session.commit.call_count == 1
        # Buffer should be empty after flush
        assert len(service._pending_assets) == 0


@pytest.mark.asyncio
async def test_asset_service_flushes_on_exit():
    """Remaining assets are flushed when exiting context."""
    mock_session = AsyncMock()
    # Mock exec to return no existing asset
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    from app.services.asset_service import AssetService

    commit_count_before_exit = 0

    async with AssetService(mock_session) as service:
        # Add 10 assets (below BATCH_SIZE)
        for i in range(10):
            await service.process_asset(
                target_id=1, task_id=1, url=f"http://test{i}.com"
            )

        # No commit yet (buffering)
        assert mock_session.commit.call_count == 0
        commit_count_before_exit = mock_session.commit.call_count

    # After exiting context, should have committed (flush in __aexit__)
    assert mock_session.commit.call_count == commit_count_before_exit + 1
