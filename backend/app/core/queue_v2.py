"""
TaskQueueV2: Advanced task queue implementation for Active Scan V2.

Features:
- Atomic operations via Lua scripts
- Visibility timeout with automatic recovery
- Exponential backoff retry mechanism
- Priority-based queue processing (CRITICAL > HIGH > NORMAL > LOW)
- Dead Letter Queue (DLQ) for failed tasks
- Comprehensive monitoring and statistics

Architecture:
- pending queue (ZSET): Tasks waiting to be processed, scored by priority
- processing queue (ZSET): Tasks currently being processed, scored by visibility timeout
- delayed queue (ZSET): Tasks scheduled for retry, scored by execution timestamp
- dlq queue (ZSET): Dead letter queue for permanently failed tasks
- task data (HASH): Task metadata and payload storage
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis

from app.core.priority import TaskPriority

logger = logging.getLogger(__name__)


class TaskQueueV2:
    """
    Advanced task queue with atomic operations and reliability features.

    Queue Structure:
    - {queue_name}:pending - ZSET with priority scores (higher score = higher priority)
    - {queue_name}:processing - ZSET with visibility timeout scores
    - {queue_name}:delayed - ZSET with execution timestamp scores
    - {queue_name}:dlq - ZSET with failure timestamp scores
    - {queue_name}:data - HASH storing task_id -> task_data JSON
    """

    # Lua script for atomic dequeue operation
    DEQUEUE_SCRIPT = """
local task_id = redis.call('ZRANGE', KEYS[1], 0, 0, 'REV')[1]
if not task_id then
    return nil
end
local task_data = redis.call('HGET', KEYS[2], task_id)
if not task_data then
    redis.call('ZREM', KEYS[1], task_id)
    return nil
end
redis.call('ZREM', KEYS[1], task_id)
redis.call('ZADD', KEYS[3], ARGV[1], task_id)
return cjson.encode({task_id, task_data})
"""

    def __init__(
        self,
        redis: Redis,
        queue_name: str = "task_queue",
        visibility_timeout: int = 300,  # 5 minutes
        max_retries: int = 3,
        base_backoff_seconds: int = 60,
    ):
        """
        Initialize TaskQueueV2.

        Args:
            redis: Redis async client
            queue_name: Base name for queue keys
            visibility_timeout: Seconds before task becomes visible again if not acked
            max_retries: Maximum retry attempts before moving to DLQ
            base_backoff_seconds: Base delay for exponential backoff (base * 2^retry_count)
        """
        self.redis = redis
        self.queue_name = queue_name
        self.visibility_timeout = visibility_timeout
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds

        # Queue keys
        self.pending_key = f"{queue_name}:pending"
        self.processing_key = f"{queue_name}:processing"
        self.delayed_key = f"{queue_name}:delayed"
        self.dlq_key = f"{queue_name}:dlq"
        self.data_key = f"{queue_name}:data"

    async def enqueue(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> None:
        """
        Enqueue a task with specified priority.

        Args:
            task_id: Unique task identifier
            task_data: Task payload (must be JSON serializable)
            priority: Task priority level (default: NORMAL)
        """
        # Store task data in hash
        task_json = json.dumps(task_data)
        await self.redis.hset(  # type: ignore[misc]
            self.data_key,
            key=task_id,
            value=task_json,
        )

        # Add to pending queue with priority score
        # Higher priority value = higher score = processed first
        await self.redis.zadd(
            self.pending_key,
            mapping={task_id: priority.value},
        )

        logger.debug(
            "Task enqueued",
            extra={
                "task_id": task_id,
                "priority": priority.name,
                "queue": self.queue_name,
            },
        )

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue highest priority task and move to processing queue.

        Uses atomic Lua script to prevent race conditions.
        Priority order: CRITICAL (3) > HIGH (2) > NORMAL (1) > LOW (0)

        Returns:
            Task data with metadata including task_id, or None if queue is empty
        """
        current_time = datetime.now(timezone.utc).timestamp()
        visibility_deadline = current_time + self.visibility_timeout

        try:
            result = await self.redis.eval(  # type: ignore[misc]
                self.DEQUEUE_SCRIPT,
                3,  # number of keys
                self.pending_key,  # KEYS[1]
                self.data_key,  # KEYS[2]
                self.processing_key,  # KEYS[3]
                str(visibility_deadline),  # ARGV[1]
            )

            if not result:
                return None

            # Parse the Lua script result
            result_list = json.loads(result)
            task_id = result_list[0]
            task_json = result_list[1]

            try:
                task_data = json.loads(task_json)
            except json.JSONDecodeError as e:
                logger.error(
                    "Invalid JSON in task data",
                    extra={"task_id": task_id, "error": str(e)},
                )
                await self._move_to_dlq(task_id, task_json)
                return None

            # Add task_id to the returned data
            result_data: Dict[str, Any] = {**task_data, "task_id": task_id}

            logger.debug(
                "Task dequeued",
                extra={
                    "task_id": task_id,
                    "visibility_timeout": self.visibility_timeout,
                },
            )

            return result_data

        except Exception as e:
            logger.error(f"Error during atomic dequeue: {e}")
            return None

    async def ack(self, task_id: str) -> None:
        """
        Acknowledge successful task completion.

        Removes task from processing queue and deletes task data.

        Args:
            task_id: Task identifier to acknowledge
        """
        # Remove from processing queue
        await self.redis.zrem(self.processing_key, task_id)

        # Delete task data
        await self.redis.hdel(self.data_key, task_id)  # type: ignore[misc]

        logger.info(
            "Task acknowledged",
            extra={"task_id": task_id},
        )

    async def nack(
        self,
        task_id: str,
        retry: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Handle task failure.

        If retry=True and retry_count < max_retries:
            - Increment retry_count
            - Calculate exponential backoff delay
            - Move to delayed queue

        If retry=False or retry_count >= max_retries:
            - Move to DLQ

        Args:
            task_id: Task identifier to nack
            retry: Whether to retry the task (default: True)
            error: Optional error message to store in task metadata
        """
        # Remove from processing queue
        await self.redis.zrem(self.processing_key, task_id)

        # Get current task data
        task_json_result = await self.redis.hget(self.data_key, task_id)  # type: ignore[misc]
        task_json = task_json_result
        if not task_json:
            logger.warning(
                "Task data missing during nack",
                extra={"task_id": task_id},
            )
            return

        try:
            task_data = json.loads(task_json)
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON during nack, moving to DLQ",
                extra={"task_id": task_id, "error": str(e)},
            )
            await self._move_to_dlq(task_id, task_json)
            return

        # Get current retry count
        retry_count = task_data.get("retry_count", 0)

        # Check if we should retry
        if retry and retry_count < self.max_retries:
            # Increment retry count
            task_data["retry_count"] = retry_count + 1

            # Store failure metadata
            if error:
                task_data["last_error"] = error
            task_data["failed_at"] = datetime.now(timezone.utc).timestamp()

            # Update task data
            updated_json = json.dumps(task_data)
            await self.redis.hset(self.data_key, key=task_id, value=updated_json)  # type: ignore[misc]

            # Calculate backoff delay
            backoff_seconds = self._calculate_backoff(retry_count)
            execute_at = datetime.now(timezone.utc).timestamp() + backoff_seconds

            # Add to delayed queue
            await self.redis.zadd(
                self.delayed_key,
                mapping={task_id: execute_at},
            )

            logger.info(
                "Task scheduled for retry",
                extra={
                    "task_id": task_id,
                    "retry_count": task_data["retry_count"],
                    "delay_seconds": backoff_seconds,
                },
            )
        else:
            # Move to DLQ
            if error:
                task_data["last_error"] = error
            task_data["failed_at"] = datetime.now(timezone.utc).timestamp()
            task_data["final_retry_count"] = retry_count

            updated_json = json.dumps(task_data)
            await self.redis.hset(self.data_key, key=task_id, value=updated_json)  # type: ignore[misc]

            await self._move_to_dlq(task_id, updated_json)

            logger.warning(
                "Task moved to DLQ",
                extra={
                    "task_id": task_id,
                    "retry_count": retry_count,
                    "max_retries": self.max_retries,
                    "retry_requested": retry,
                },
            )

    async def recover_expired_tasks(self) -> int:
        """
        Recover tasks with expired visibility timeout.

        Moves tasks from processing queue back to pending queue
        if their visibility timeout has expired.

        Increments timeout_count in task metadata.

        Returns:
            Number of tasks recovered
        """
        current_time = datetime.now(timezone.utc).timestamp()

        # Get all expired tasks (score <= current_time)
        expired_tasks = await self.redis.zrangebyscore(
            self.processing_key,
            min=0,
            max=current_time,
        )

        if not expired_tasks:
            return 0

        recovered_count = 0

        for task_id_bytes in expired_tasks:
            task_id = (
                task_id_bytes.decode()
                if isinstance(task_id_bytes, bytes)
                else task_id_bytes
            )

            # Get task data
            task_json_result = await self.redis.hget(self.data_key, task_id)  # type: ignore[misc]
            task_json = task_json_result
            if not task_json:
                # Task data missing - remove from processing
                await self.redis.zrem(self.processing_key, task_id)
                continue

            try:
                task_data = json.loads(task_json)
            except json.JSONDecodeError:
                # Invalid JSON - move to DLQ
                await self.redis.zrem(self.processing_key, task_id)
                await self._move_to_dlq(task_id, task_json)
                continue

            # Increment timeout count
            task_data["timeout_count"] = task_data.get("timeout_count", 0) + 1

            # Update task data
            updated_json = json.dumps(task_data)
            await self.redis.hset(self.data_key, key=task_id, value=updated_json)  # type: ignore[misc]

            # Get original priority
            priority = task_data.get("priority", TaskPriority.NORMAL.value)

            # Remove from processing
            await self.redis.zrem(self.processing_key, task_id)

            # Add back to pending with original priority
            await self.redis.zadd(
                self.pending_key,
                mapping={task_id: priority},
            )

            recovered_count += 1

            logger.info(
                "Task recovered from processing",
                extra={
                    "task_id": task_id,
                    "timeout_count": task_data["timeout_count"],
                },
            )

        return recovered_count

    async def process_delayed_tasks(self) -> int:
        """
        Move ready delayed tasks back to pending queue.

        Checks delayed queue for tasks whose execution time has arrived
        (score <= current_time) and moves them to pending queue.

        Returns:
            Number of tasks processed
        """
        current_time = datetime.now(timezone.utc).timestamp()

        # Get all ready tasks (score <= current_time)
        ready_tasks = await self.redis.zrangebyscore(
            self.delayed_key,
            min=0,
            max=current_time,
        )

        if not ready_tasks:
            return 0

        processed_count = 0

        for task_id_bytes in ready_tasks:
            task_id = (
                task_id_bytes.decode()
                if isinstance(task_id_bytes, bytes)
                else task_id_bytes
            )

            # Get task data to retrieve priority
            task_json_result = await self.redis.hget(self.data_key, task_id)  # type: ignore[misc]
            task_json = task_json_result
            if not task_json:
                # Task data missing - remove from delayed
                await self.redis.zrem(self.delayed_key, task_id)
                continue

            try:
                task_data = json.loads(task_json)
            except json.JSONDecodeError:
                # Invalid JSON - move to DLQ
                await self.redis.zrem(self.delayed_key, task_id)
                await self._move_to_dlq(task_id, task_json)
                continue

            # Get priority
            priority = task_data.get("priority", TaskPriority.NORMAL.value)

            # Remove from delayed queue
            await self.redis.zrem(self.delayed_key, task_id)

            # Add to pending queue with priority
            await self.redis.zadd(
                self.pending_key,
                mapping={task_id: priority},
            )

            processed_count += 1

            logger.info(
                "Delayed task moved to pending",
                extra={"task_id": task_id, "priority": priority},
            )

        return processed_count

    async def get_stats(self) -> Dict[str, int]:
        """
        Get statistics for all queues.

        Returns:
            Dictionary with counts for pending, processing, delayed, and dlq
        """
        pending_count = await self.redis.zcard(self.pending_key)
        processing_count = await self.redis.zcard(self.processing_key)
        delayed_count = await self.redis.zcard(self.delayed_key)
        dlq_count = await self.redis.zcard(self.dlq_key)

        return {
            "pending": pending_count,
            "processing": processing_count,
            "delayed": delayed_count,
            "dlq": dlq_count,
        }

    async def get_queue_size(self, queue_type: str) -> int:
        """
        Get size of specific queue.

        Args:
            queue_type: One of 'pending', 'processing', 'delayed', 'dlq'

        Returns:
            Number of tasks in the specified queue
        """
        queue_map = {
            "pending": self.pending_key,
            "processing": self.processing_key,
            "delayed": self.delayed_key,
            "dlq": self.dlq_key,
        }

        key = queue_map.get(queue_type)
        if not key:
            raise ValueError(f"Invalid queue_type: {queue_type}")

        size = await self.redis.zcard(key)
        return int(size)

    async def get_dlq_tasks(self) -> List[str]:
        """
        Get all task IDs in the DLQ.

        Returns:
            List of task IDs in DLQ
        """
        task_ids = await self.redis.zrange(self.dlq_key, 0, -1)
        return [
            task_id.decode() if isinstance(task_id, bytes) else task_id
            for task_id in task_ids
        ]

    def _calculate_backoff(self, retry_count: int) -> float:
        """
        Calculate exponential backoff delay.

        Formula: base_backoff_seconds * (2 ^ retry_count)

        Args:
            retry_count: Current retry attempt (0-indexed)

        Returns:
            Delay in seconds
        """
        return float(self.base_backoff_seconds * (2**retry_count))

    async def _move_to_dlq(self, task_id: str, task_json: str) -> None:
        """
        Move task to Dead Letter Queue.

        Args:
            task_id: Task identifier
            task_json: Task data JSON (for logging purposes)
        """
        current_time = datetime.now(timezone.utc).timestamp()

        await self.redis.zadd(
            self.dlq_key,
            mapping={task_id: current_time},
        )

        logger.warning(
            "Task moved to DLQ",
            extra={"task_id": task_id},
        )
