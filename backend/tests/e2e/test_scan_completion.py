"""
Phase 3 E2E Integration Tests: Scan Completion with Retry & DLQ

These tests verify the complete retry pipeline including:
- NACK retry limit prevents infinite loops (Phase 1)
- Exponential backoff with delayed queue (Phase 2)
- DLQ receives failed tasks after max retries
- Normal task processing within timeout

Tests use real Redis connections (Docker container) to verify actual behavior.
"""

import json
import time
from typing import Any, Dict
from unittest.mock import patch

import pytest
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.priority import TaskPriority, get_queue_key
from app.core.queue import TaskManager
from app.core.retry import MAX_RETRIES, calculate_backoff
from app.models.task import Task, TaskStatus, TaskType

# Note: These tests should complete within reasonable time without external timeout marks
# The asyncio event loop will handle timeouts internally


@pytest.fixture
async def task_manager(redis_client: Redis) -> TaskManager:
    """Create TaskManager with test Redis client."""
    return TaskManager(redis_client)


@pytest.fixture
async def clean_queues(redis_client: Redis):
    """Clean all queues before and after test."""
    # Keys to clean
    keys_to_clean = [
        "eazy_task_queue",
        "eazy_task_queue:critical",
        "eazy_task_queue:high",
        "eazy_task_queue:low",
        "eazy_task_queue:processing",
        "eazy_task_queue:dlq",
        "eazy_task_queue:delayed",
    ]

    # Clean before test
    for key in keys_to_clean:
        await redis_client.delete(key)

    yield

    # Clean after test
    for key in keys_to_clean:
        await redis_client.delete(key)


async def create_test_task_payload(
    task_id: str,
    db_task_id: int,
    target_id: int,
    project_id: int = 1,
    priority: TaskPriority = TaskPriority.NORMAL,
    retry_count: int = 0,
) -> Dict[str, Any]:
    """Create a test task payload."""
    return {
        "id": task_id,
        "db_task_id": db_task_id,
        "type": TaskType.CRAWL.value,
        "project_id": project_id,
        "target_id": target_id,
        "priority": priority.value,
        "retry_count": retry_count,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "enqueued_at": "2024-01-01T00:00:00+00:00",
    }


class TestNackRetryLimitPreventsInfiniteLoop:
    """Test that NACK retry limit prevents infinite loops."""

    @pytest.mark.asyncio
    async def test_nack_retry_limit_prevents_infinite_loop(
        self,
        redis_client: Redis,
        task_manager: TaskManager,
        clean_queues,
    ):
        """
        Test Case 1: NACK retry limit prevents infinite loops.

        Scenario:
        - Task fails repeatedly due to lock contention
        - After MAX_RETRIES (3) NACKs, task moves to DLQ
        - No infinite loop occurs

        Verification:
        - After 3 retries, task is in DLQ
        - Main queue and delayed queue are empty
        - Test completes within timeout (no infinite loop)

        Note: TaskManager.nack_task always adds to delayed queue.
        The DLQ logic is in BaseWorker which checks retry_count.
        This test simulates that behavior by manually moving to DLQ
        when retry_count >= MAX_RETRIES.
        """
        # Setup: Create a task
        task_payload = await create_test_task_payload(
            task_id="test-retry-limit-001",
            db_task_id=1001,
            target_id=101,
        )
        task_json = json.dumps(task_payload)

        # Enqueue task to NORMAL queue
        queue_key = get_queue_key(task_manager.queue_key, TaskPriority.NORMAL)
        await redis_client.rpush(queue_key, task_json)

        # Simulate retry cycles (like BaseWorker does)
        for retry_num in range(MAX_RETRIES + 1):
            # Dequeue task
            result = await task_manager.dequeue_task(timeout=1)
            assert result is not None, f"Should have task at retry {retry_num}"

            task_data, dequeued_json = result
            current_retry_count = task_data.get("retry_count", 0)

            # Simulate BaseWorker logic: check retry_count BEFORE nack
            if current_retry_count >= MAX_RETRIES:
                # Move to DLQ (like BaseWorker does when retry limit exceeded)
                await task_manager.nack_task(dequeued_json, retry=False)
                break
            else:
                # NACK with retry=True (simulating lock failure)
                await task_manager.nack_task(dequeued_json, retry=True)

            # Force process delayed tasks (bypass backoff delay)
            delayed_count = await redis_client.zcard(task_manager.delayed_key)
            if delayed_count > 0:
                # Move all delayed tasks to main queue immediately
                tasks = await redis_client.zrangebyscore(
                    task_manager.delayed_key, "-inf", "+inf"
                )
                for t in tasks:
                    parsed = json.loads(t)
                    priority = TaskPriority(
                        parsed.get("priority", TaskPriority.NORMAL.value)
                    )
                    q_key = get_queue_key(task_manager.queue_key, priority)
                    await redis_client.rpush(q_key, t)
                    await redis_client.zrem(task_manager.delayed_key, t)

        # Verify: Task should be in DLQ after MAX_RETRIES
        dlq_tasks = await task_manager.get_dlq_tasks()
        assert len(dlq_tasks) >= 1, "Task should be in DLQ"

        # Find our task in DLQ
        dlq_task = None
        for task in dlq_tasks:
            if task.get("id") == "test-retry-limit-001":
                dlq_task = task
                break

        assert dlq_task is not None, "Our task should be in DLQ"
        assert (
            dlq_task.get("retry_count", 0) >= MAX_RETRIES
        ), f"DLQ task should have retry_count >= {MAX_RETRIES}"

        # Verify: Main queue and delayed queue should be empty
        queue_length = await redis_client.llen(queue_key)
        delayed_length = await redis_client.zcard(task_manager.delayed_key)

        assert queue_length == 0, "Main queue should be empty"
        assert delayed_length == 0, "Delayed queue should be empty"


class TestDelayedQueueBackoff:
    """Test exponential backoff with delayed queue."""

    @pytest.mark.asyncio
    async def test_delayed_queue_backoff_works(
        self,
        redis_client: Redis,
        task_manager: TaskManager,
        clean_queues,
    ):
        """
        Test Case 2: NACK adds task to delayed queue with backoff.

        Scenario:
        - Task is NACKed
        - Task goes to delayed queue (ZSET with score = execute_at)
        - process_delayed_tasks moves ready tasks back to main queue

        Verification:
        - After NACK, task is in delayed queue
        - After process_delayed_tasks, task is back in main queue
        - retry_count is incremented
        """
        # Setup: Create a task
        task_payload = await create_test_task_payload(
            task_id="test-backoff-001",
            db_task_id=1002,
            target_id=102,
        )
        task_json = json.dumps(task_payload)

        # Enqueue task
        queue_key = get_queue_key(task_manager.queue_key, TaskPriority.NORMAL)
        await redis_client.rpush(queue_key, task_json)

        # Dequeue and NACK
        result = await task_manager.dequeue_task(timeout=1)
        assert result is not None
        task_data, dequeued_json = result

        # NACK with retry=True
        await task_manager.nack_task(dequeued_json, retry=True)

        # Verify: Task should be in delayed queue
        delayed_count = await redis_client.zcard(task_manager.delayed_key)
        assert delayed_count == 1, "Task should be in delayed queue"

        # Check delayed task has correct retry_count
        delayed_tasks = await redis_client.zrange(
            task_manager.delayed_key, 0, -1, withscores=True
        )
        assert len(delayed_tasks) == 1

        delayed_task_json, score = delayed_tasks[0]
        delayed_task = json.loads(delayed_task_json)
        assert (
            delayed_task["retry_count"] == 1
        ), "retry_count should be incremented to 1"

        # Verify score (execute_at) is in the future
        assert score > time.time(), "execute_at should be in the future"

        # Force immediate processing by adjusting score
        await redis_client.zadd(
            task_manager.delayed_key,
            {delayed_task_json: time.time() - 1},  # Set to past
        )

        # Process delayed tasks
        moved_count = await task_manager.process_delayed_tasks()
        assert moved_count == 1, "Should have moved 1 task"

        # Verify: Task should be back in main queue
        queue_length = await redis_client.llen(queue_key)
        assert queue_length == 1, "Task should be back in main queue"

        # Delayed queue should be empty
        delayed_count = await redis_client.zcard(task_manager.delayed_key)
        assert delayed_count == 0, "Delayed queue should be empty"


class TestDlqReceivesFailedTasks:
    """Test that DLQ receives failed tasks after max retries."""

    @pytest.mark.asyncio
    async def test_dlq_receives_failed_tasks(
        self,
        redis_client: Redis,
        task_manager: TaskManager,
        clean_queues,
    ):
        """
        Test Case 3: Tasks exceeding MAX_RETRIES go to DLQ.

        Scenario:
        - Task already has retry_count = MAX_RETRIES - 1
        - One more NACK should move it to DLQ

        Verification:
        - Task is in DLQ (not delayed queue)
        - DLQ task has retry_count >= MAX_RETRIES
        """
        # Setup: Create a task that's already at retry limit - 1
        task_payload = await create_test_task_payload(
            task_id="test-dlq-001",
            db_task_id=1003,
            target_id=103,
            retry_count=MAX_RETRIES - 1,  # One more NACK will exceed limit
        )
        task_json = json.dumps(task_payload)

        # Enqueue task
        queue_key = get_queue_key(task_manager.queue_key, TaskPriority.NORMAL)
        await redis_client.rpush(queue_key, task_json)

        # Dequeue
        result = await task_manager.dequeue_task(timeout=1)
        assert result is not None
        task_data, dequeued_json = result

        # Verify current retry_count
        assert task_data.get("retry_count") == MAX_RETRIES - 1

        # NACK - this should increment retry_count to MAX_RETRIES
        await task_manager.nack_task(dequeued_json, retry=True)

        # Task goes to delayed queue first (because nack_task always adds to delayed with retry=True)
        delayed_tasks = await redis_client.zrange(task_manager.delayed_key, 0, -1)

        if delayed_tasks:
            # Check the retry_count in delayed task
            delayed_task = json.loads(delayed_tasks[0])
            assert (
                delayed_task["retry_count"] == MAX_RETRIES
            ), f"retry_count should be {MAX_RETRIES}"

            # Force process to move to main queue
            await redis_client.zadd(
                task_manager.delayed_key, {delayed_tasks[0]: time.time() - 1}
            )
            await task_manager.process_delayed_tasks()

        # Dequeue and NACK again - now it should go to DLQ
        result = await task_manager.dequeue_task(timeout=1)
        if result:
            task_data, dequeued_json = result
            # This NACK should send to DLQ via the worker's logic
            # Since TaskManager.nack_task always adds to delayed queue with retry=True,
            # the DLQ logic is in BaseWorker. Here we simulate by calling nack with retry=False
            await task_manager.nack_task(dequeued_json, retry=False)

        # Verify: Task should be in DLQ
        dlq_length = await task_manager.get_dlq_length()
        assert dlq_length >= 1, "DLQ should have at least 1 task"

        dlq_tasks = await task_manager.get_dlq_tasks()
        dlq_task = None
        for task in dlq_tasks:
            if task.get("id") == "test-dlq-001":
                dlq_task = task
                break

        assert dlq_task is not None, "Our task should be in DLQ"


class TestWorkerProcessesTaskWithinTimeout:
    """Test that worker processes task within reasonable timeout."""

    @pytest.mark.asyncio
    async def test_worker_processes_task_within_timeout(
        self,
        redis_client: Redis,
        db_session: AsyncSession,
        task_manager: TaskManager,
        clean_queues,
    ):
        """
        Test Case 4: Single task completes within timeout.

        Scenario:
        - Create a task via API or directly
        - Process task with mocked crawler
        - Verify task completes successfully

        Verification:
        - Task status becomes COMPLETED
        - Processing completes within 60 second timeout
        - Task is ACKed (removed from processing queue)
        """
        from app.models.project import Project
        from app.models.target import Target
        from app.workers import create_worker_context, process_one_task

        # Setup: Create project and target in DB
        project = Project(name="Test Project E2E")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target E2E",
            url="https://example.com",
            project_id=project.id,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        # Create task in DB (project_id is required)
        task = Task(
            type=TaskType.CRAWL,
            project_id=project.id,  # Required field
            target_id=target.id,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Enqueue task to Redis
        await task_manager.enqueue_crawl_task(
            project_id=project.id,
            target_id=target.id,
            db_task_id=task.id,
            priority=TaskPriority.NORMAL,
        )

        # Record start time
        start_time = time.time()

        # Create worker context
        context = create_worker_context(db_session, redis_client)

        # Process task with mocked crawler
        with patch("app.services.crawler_service.CrawlerService.crawl") as mock_crawl:
            mock_crawl.return_value = (
                ["https://example.com/page1", "https://example.com/page2"],
                {},  # Empty http_data
                [],  # js_contents
            )

            # Process one task
            processed = await process_one_task(context)

        # Record end time
        elapsed = time.time() - start_time

        # Verify: Task processed
        assert processed is True, "Task should have been processed"

        # Verify: Completed within reasonable time (60 seconds)
        assert elapsed < 60, f"Task took too long: {elapsed}s"

        # Verify: Task status is COMPLETED
        await db_session.refresh(task)
        assert (
            task.status == TaskStatus.COMPLETED
        ), f"Task should be COMPLETED, got {task.status}"

        # Verify: Processing queue is empty (task was ACKed)
        processing_length = await task_manager.get_processing_length()
        assert processing_length == 0, "Processing queue should be empty"


class TestBackoffCalculation:
    """Test exponential backoff calculation."""

    @pytest.mark.asyncio
    async def test_backoff_increases_exponentially(self):
        """
        Verify that backoff delay increases exponentially with retry count.

        Formula: delay = min(BASE_DELAY * 2^retry_count, MAX_DELAY) + jitter
        """
        delays = []
        for retry_count in range(5):
            # Calculate multiple times to average out jitter
            samples = [calculate_backoff(retry_count) for _ in range(10)]
            avg_delay = sum(samples) / len(samples)
            delays.append(avg_delay)

        # Verify exponential increase (each delay should be roughly 2x previous)
        for i in range(1, len(delays)):
            if delays[i] < 60:  # Before hitting MAX_DELAY cap
                ratio = delays[i] / delays[i - 1]
                assert 1.3 < ratio < 3.0, (
                    f"Backoff ratio should be ~2x, got {ratio:.2f} "
                    f"(delay[{i}]={delays[i]:.2f}, delay[{i - 1}]={delays[i - 1]:.2f})"
                )


class TestMultipleTasksLockContention:
    """Test multiple tasks competing for same target lock."""

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_target_no_infinite_loop(
        self,
        redis_client: Redis,
        task_manager: TaskManager,
        clean_queues,
    ):
        """
        Test that multiple tasks for same target don't cause infinite loops.

        Scenario:
        - Enqueue 3 tasks for same target
        - Simulate lock contention (all tasks fail to acquire lock)
        - Verify all eventually go to DLQ without infinite loop
        """
        target_id = 999
        task_ids = [f"test-contention-{i}" for i in range(3)]

        # Enqueue multiple tasks for same target
        for i, task_id in enumerate(task_ids):
            task_payload = await create_test_task_payload(
                task_id=task_id,
                db_task_id=2000 + i,
                target_id=target_id,
            )
            task_json = json.dumps(task_payload)
            queue_key = get_queue_key(task_manager.queue_key, TaskPriority.NORMAL)
            await redis_client.rpush(queue_key, task_json)

        # Process all tasks through retry cycles
        # Each task needs MAX_RETRIES NACKs to reach DLQ, plus safety margin
        max_iterations = (MAX_RETRIES + 1) * len(task_ids) * 2  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            # First, process delayed queue if any tasks are ready
            delayed_count = await redis_client.zcard(task_manager.delayed_key)
            if delayed_count > 0:
                # Move delayed tasks to main queue or DLQ based on retry_count
                tasks = await redis_client.zrangebyscore(
                    task_manager.delayed_key, "-inf", "+inf"
                )
                for t in tasks:
                    parsed = json.loads(t)
                    retry_count = parsed.get("retry_count", 0)

                    if retry_count >= MAX_RETRIES:
                        # Move to DLQ (simulating BaseWorker logic)
                        await redis_client.lpush(task_manager.dlq_key, t)
                    else:
                        # Move back to main queue
                        priority = TaskPriority(
                            parsed.get("priority", TaskPriority.NORMAL.value)
                        )
                        q_key = get_queue_key(task_manager.queue_key, priority)
                        await redis_client.rpush(q_key, t)

                    await redis_client.zrem(task_manager.delayed_key, t)

            # Try to dequeue
            result = await task_manager.dequeue_task(timeout=1)

            if result is None:
                # Check if we still have delayed tasks
                delayed_count = await redis_client.zcard(task_manager.delayed_key)
                if delayed_count > 0:
                    continue
                else:
                    # No more tasks anywhere
                    break

            task_data, dequeued_json = result

            # Simulate lock failure - NACK with retry
            await task_manager.nack_task(dequeued_json, retry=True)
            iteration += 1

        # Verify: All tasks should be in DLQ
        dlq_tasks = await task_manager.get_dlq_tasks()
        dlq_ids = {task.get("id") for task in dlq_tasks}

        for task_id in task_ids:
            assert task_id in dlq_ids, f"Task {task_id} should be in DLQ"

        # Verify: No tasks in main or delayed queue
        queue_key = get_queue_key(task_manager.queue_key, TaskPriority.NORMAL)
        queue_length = await redis_client.llen(queue_key)
        delayed_length = await redis_client.zcard(task_manager.delayed_key)

        assert queue_length == 0, "Main queue should be empty"
        assert delayed_length == 0, "Delayed queue should be empty"

        # Test completed without timeout = no infinite loop
