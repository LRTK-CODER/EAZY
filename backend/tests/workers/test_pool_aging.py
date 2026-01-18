"""
Sprint 3.1: Aging Task Background Worker Tests

TDD tests for WorkerPool aging task that promotes aged tasks periodically.
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest


class TestAgingTaskConfig:
    """Test aging task configuration in WorkerPoolConfig."""

    def test_aging_enabled_default_false(self):
        """Aging should be disabled by default."""
        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig()
        assert config.aging_enabled is False

    def test_aging_enabled_from_env(self):
        """Aging can be enabled via environment variable."""
        from app.workers.pool import WorkerPoolConfig

        with patch.dict(os.environ, {"WORKER_AGING_ENABLED": "true"}):
            config = WorkerPoolConfig.from_env()
            assert config.aging_enabled is True

    def test_aging_interval_default(self):
        """Default aging interval should be 60 seconds."""
        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig()
        assert config.aging_interval == 60

    def test_aging_interval_from_env(self):
        """Aging interval can be set via environment variable."""
        from app.workers.pool import WorkerPoolConfig

        with patch.dict(os.environ, {"WORKER_AGING_INTERVAL": "30"}):
            config = WorkerPoolConfig.from_env()
            assert config.aging_interval == 30


class TestAgingTaskLifecycle:
    """Test aging task lifecycle management."""

    @pytest.mark.asyncio
    async def test_aging_task_starts_when_enabled(self):
        """Aging task should start when aging_enabled is True."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=1,
            aging_enabled=True,
            aging_interval=1,
        )
        pool = WorkerPool(config)

        aging_called = asyncio.Event()

        async def track_aging():
            aging_called.set()
            # Wait briefly then return
            await asyncio.sleep(0.05)

        with patch.object(pool, "_run_aging_task", side_effect=track_aging):
            with patch.object(pool, "_run_worker_supervised", new_callable=AsyncMock):
                mock_engine = AsyncMock()
                mock_engine.dispose = AsyncMock()
                with patch(
                    "app.workers.pool.create_async_engine", return_value=mock_engine
                ):
                    # Start and immediately stop
                    start_task = asyncio.create_task(pool.start())
                    await asyncio.sleep(0.1)
                    await pool.stop()
                    await start_task

                    # Verify aging task was started
                    assert aging_called.is_set()

    @pytest.mark.asyncio
    async def test_aging_task_not_started_when_disabled(self):
        """Aging task should not start when aging_enabled is False."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=1,
            aging_enabled=False,
        )
        pool = WorkerPool(config)

        aging_called = asyncio.Event()

        async def track_aging():
            aging_called.set()

        with patch.object(pool, "_run_aging_task", side_effect=track_aging):
            with patch.object(pool, "_run_worker_supervised", new_callable=AsyncMock):
                mock_engine = AsyncMock()
                mock_engine.dispose = AsyncMock()
                with patch(
                    "app.workers.pool.create_async_engine", return_value=mock_engine
                ):
                    start_task = asyncio.create_task(pool.start())
                    await asyncio.sleep(0.1)
                    await pool.stop()
                    await start_task

                    # Verify aging task was NOT started
                    assert not aging_called.is_set()

    @pytest.mark.asyncio
    async def test_aging_task_stops_on_shutdown(self):
        """Aging task should be cancelled on pool shutdown."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=1,
            aging_enabled=True,
            aging_interval=60,
        )
        pool = WorkerPool(config)

        aging_task_started = asyncio.Event()
        aging_task_stopped = asyncio.Event()

        async def mock_aging_task():
            aging_task_started.set()
            try:
                await asyncio.sleep(3600)  # Long sleep
            except asyncio.CancelledError:
                aging_task_stopped.set()
                raise

        with patch.object(pool, "_run_aging_task", side_effect=mock_aging_task):
            with patch.object(pool, "_run_worker_supervised", new_callable=AsyncMock):
                mock_engine = AsyncMock()
                mock_engine.dispose = AsyncMock()
                with patch(
                    "app.workers.pool.create_async_engine", return_value=mock_engine
                ):
                    start_task = asyncio.create_task(pool.start())
                    await asyncio.wait_for(aging_task_started.wait(), timeout=1.0)
                    await pool.stop()
                    await start_task

                    # Verify aging task was stopped
                    assert aging_task_stopped.is_set()


class TestAgingTaskExecution:
    """Test aging task execution behavior."""

    @pytest.mark.asyncio
    async def test_aging_task_calls_promote_aged_tasks(self):
        """Aging task should call promote_aged_tasks on TaskManager."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=0,
            aging_enabled=True,
            aging_interval=1,
        )
        pool = WorkerPool(config)
        pool._shutdown_event = asyncio.Event()

        with patch("app.workers.pool.Redis") as mock_redis_cls:
            mock_redis = AsyncMock()
            mock_redis_cls.from_url.return_value = mock_redis

            with patch("app.workers.pool.TaskManager") as mock_tm_cls:
                mock_tm = AsyncMock()
                mock_tm.promote_aged_tasks = AsyncMock(return_value=0)
                mock_tm_cls.return_value = mock_tm

                # Run aging task briefly
                async def stop_after_delay():
                    await asyncio.sleep(0.2)
                    pool._shutdown_event.set()

                asyncio.create_task(stop_after_delay())
                await pool._run_aging_task()

                # Verify promote_aged_tasks was called
                mock_tm.promote_aged_tasks.assert_called()

    @pytest.mark.asyncio
    async def test_aging_task_runs_periodically(self):
        """Aging task should run multiple times with interval."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=0,
            aging_enabled=True,
            aging_interval=0.1,  # 100ms for fast testing
        )
        pool = WorkerPool(config)
        pool._shutdown_event = asyncio.Event()

        call_count = 0

        async def mock_promote(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return 0

        with patch("app.workers.pool.Redis") as mock_redis_cls:
            mock_redis = AsyncMock()
            mock_redis_cls.from_url.return_value = mock_redis

            with patch("app.workers.pool.TaskManager") as mock_tm_cls:
                mock_tm = AsyncMock()
                mock_tm.promote_aged_tasks = mock_promote
                mock_tm_cls.return_value = mock_tm

                # Run for ~350ms (should get 3-4 calls at 100ms interval)
                async def stop_after_delay():
                    await asyncio.sleep(0.35)
                    pool._shutdown_event.set()

                asyncio.create_task(stop_after_delay())
                await pool._run_aging_task()

                # Should have been called multiple times
                assert call_count >= 3

    @pytest.mark.asyncio
    async def test_aging_task_handles_redis_error(self):
        """Aging task should handle Redis errors gracefully."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=0,
            aging_enabled=True,
            aging_interval=0.1,
        )
        pool = WorkerPool(config)
        pool._shutdown_event = asyncio.Event()

        error_count = 0
        success_count = 0

        async def mock_promote_with_errors(*args, **kwargs):
            nonlocal error_count, success_count
            if error_count < 2:
                error_count += 1
                raise Exception("Redis connection error")
            success_count += 1
            return 0

        with patch("app.workers.pool.Redis") as mock_redis_cls:
            mock_redis = AsyncMock()
            mock_redis_cls.from_url.return_value = mock_redis

            with patch("app.workers.pool.TaskManager") as mock_tm_cls:
                mock_tm = AsyncMock()
                mock_tm.promote_aged_tasks = mock_promote_with_errors
                mock_tm_cls.return_value = mock_tm

                async def stop_after_delay():
                    await asyncio.sleep(0.35)
                    pool._shutdown_event.set()

                asyncio.create_task(stop_after_delay())

                # Should not raise, should continue after errors
                await pool._run_aging_task()

                # Verify it continued after errors
                assert error_count == 2
                assert success_count >= 1

    @pytest.mark.asyncio
    async def test_aging_task_logs_promotion_count(self):
        """Aging task should log when tasks are promoted."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=0,
            aging_enabled=True,
            aging_interval=0.1,
        )
        pool = WorkerPool(config)
        pool._shutdown_event = asyncio.Event()

        with patch("app.workers.pool.Redis") as mock_redis_cls:
            mock_redis = AsyncMock()
            mock_redis_cls.from_url.return_value = mock_redis

            with patch("app.workers.pool.TaskManager") as mock_tm_cls:
                mock_tm = AsyncMock()
                mock_tm.promote_aged_tasks = AsyncMock(return_value=5)
                mock_tm_cls.return_value = mock_tm

                with patch("app.workers.pool.logger") as mock_logger:

                    async def stop_after_delay():
                        await asyncio.sleep(0.15)
                        pool._shutdown_event.set()

                    asyncio.create_task(stop_after_delay())
                    await pool._run_aging_task()

                    # Verify info log was called with promotion count
                    info_calls = [
                        call
                        for call in mock_logger.info.call_args_list
                        if "Promoted" in str(call) or "count" in str(call)
                    ]
                    assert len(info_calls) > 0


class TestAgingTaskIntegration:
    """Integration tests for aging task."""

    @pytest.mark.asyncio
    async def test_aging_task_with_worker_pool(self):
        """Aging task should work alongside worker tasks."""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=2,
            aging_enabled=True,
            aging_interval=0.1,
        )
        pool = WorkerPool(config)

        aging_ran = asyncio.Event()
        workers_ran = asyncio.Event()

        async def track_aging(*args, **kwargs):
            aging_ran.set()
            # Immediately return to not block test
            return

        async def track_worker(*args, **kwargs):
            workers_ran.set()
            # Immediately return to not block test
            return

        with patch.object(pool, "_run_aging_task", side_effect=track_aging):
            with patch.object(pool, "_run_worker_supervised", side_effect=track_worker):
                mock_engine = AsyncMock()
                mock_engine.dispose = AsyncMock()
                with patch(
                    "app.workers.pool.create_async_engine", return_value=mock_engine
                ):
                    start_task = asyncio.create_task(pool.start())
                    await asyncio.sleep(0.1)
                    await pool.stop()
                    await start_task

                    # Both aging and workers should have started
                    assert aging_ran.is_set()
                    assert workers_ran.is_set()

    @pytest.mark.asyncio
    async def test_aging_promotes_old_tasks(self, redis_client):
        """E2E test: aging should actually promote old tasks."""
        import json
        import uuid
        from datetime import datetime, timedelta, timezone

        from app.core.priority import AgingConfig, TaskPriority
        from app.core.queue import TaskManager

        # Use unique queue prefix to avoid interference from Docker workers
        test_id = uuid.uuid4().hex[:8]
        queue_base = f"test_aging_{test_id}"
        queue_key = f"{queue_base}:low"
        normal_queue = queue_base

        # Create TaskManager with custom queue key
        task_manager = TaskManager(redis_client)
        task_manager.queue_key = queue_base  # Override for testing

        # Clean up any existing tasks first
        await redis_client.delete(queue_key, normal_queue)

        # Create an old task (enqueued 10 minutes ago)
        old_time = datetime.now(timezone.utc) - timedelta(seconds=400)
        old_task = {
            "type": "crawl",
            "target_id": 1,
            "priority": TaskPriority.LOW.value,
            "enqueued_at": old_time.isoformat(),
        }

        # Enqueue directly to LOW queue (use rpush for FIFO - items read from left)
        await redis_client.rpush(queue_key, json.dumps(old_task))

        # Verify task is in LOW queue
        low_count = await redis_client.llen(queue_key)
        assert low_count == 1, f"Expected 1 task in LOW queue, got {low_count}"

        # Run promote with short threshold
        config = AgingConfig(low_to_normal_seconds=300)  # 5 minutes
        promoted = await task_manager.promote_aged_tasks(config)

        # Verify task was promoted
        assert promoted == 1, f"Expected 1 promoted, got {promoted}"

        # Verify task is now in NORMAL queue
        tasks = await redis_client.lrange(normal_queue, 0, -1)
        assert len(tasks) == 1, f"Expected 1 task in NORMAL queue, got {len(tasks)}"

        # Cleanup
        await redis_client.delete(queue_key, normal_queue)
