"""
BaseWorker and WorkerContext for EAZY worker infrastructure.

Phase 3: Architecture Improvement
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dlq import DLQManager
from app.core.queue import TaskManager
from app.core.recovery import OrphanRecovery
from app.core.retry import MAX_RETRIES
from app.core.structured_logger import get_logger
from app.core.utils import utc_now
from app.models.task import Task, TaskStatus, TaskType

logger = get_logger(__name__)


@dataclass
class WorkerContext:
    """
    Dependency injection container for workers.

    Contains all shared dependencies that workers need to function:
    - session: Database session for persistence
    - task_manager: Queue management for task dequeue/ack/nack
    - dlq_manager: Dead letter queue management
    - orphan_recovery: Heartbeat and orphan task recovery
    """

    session: AsyncSession
    task_manager: TaskManager
    dlq_manager: DLQManager
    orphan_recovery: OrphanRecovery


@dataclass
class TaskResult:
    """
    Result of task execution.

    Encapsulates the outcome of a worker's execute() method:
    - _success: Whether the task completed successfully
    - data: Any data to store with the result
    - error: Error message if the task failed
    - _cancelled: Whether the task was cancelled by user
    - _skipped: Whether the task was skipped (e.g., lock unavailable)
    """

    _success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    _cancelled: bool = False
    _skipped: bool = False

    @property
    def success(self) -> bool:
        """Whether the task completed successfully."""
        return self._success

    @property
    def cancelled(self) -> bool:
        """Whether the task was cancelled by user."""
        return self._cancelled

    @property
    def skipped(self) -> bool:
        """Whether the task was skipped."""
        return self._skipped

    @property
    def status(self) -> str:
        """Return the status string."""
        if self._skipped:
            return "skipped"
        if self._cancelled:
            return "cancelled"
        if self._success:
            return "success"
        return "failed"

    @classmethod
    def create_success(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create a successful result."""
        return cls(_success=True, data=data)

    @classmethod
    def create_failure(
        cls, error: str, data: Optional[Dict[str, Any]] = None
    ) -> "TaskResult":
        """Create a failure result."""
        return cls(_success=False, data=data or {}, error=error)

    @classmethod
    def create_cancelled(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create a cancelled result."""
        return cls(_success=True, data=data, _cancelled=True)

    @classmethod
    def create_skipped(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create a skipped result (e.g., lock unavailable)."""
        return cls(_success=False, data=data, _skipped=True)

    def to_json(self) -> str:
        """Serialize data to JSON string."""
        return json.dumps(self.data)


class BaseWorker(ABC):
    """
    Abstract base class for all workers.

    Provides common functionality:
    - Task lifecycle management (status updates)
    - Heartbeat integration
    - ACK/NACK handling
    - Error handling with classification

    Subclasses must implement:
    - task_type property: The TaskType this worker handles
    - execute() method: The actual task logic
    """

    def __init__(self, context: WorkerContext):
        """Initialize worker with context."""
        self.context = context
        self.session = context.session
        self.task_manager = context.task_manager

    @property
    @abstractmethod
    def task_type(self) -> TaskType:
        """Return the task type this worker handles."""
        pass

    @abstractmethod
    async def execute(self, task_data: Dict[str, Any], task_record: Task) -> TaskResult:
        """
        Execute the task - must be implemented by subclass.

        Args:
            task_data: Task data from Redis queue
            task_record: Task record from database

        Returns:
            TaskResult indicating success, failure, or cancellation
        """
        pass

    async def process(self, task_data: Dict[str, Any], task_json: str) -> bool:
        """
        Process a task with full lifecycle management.

        This method handles:
        1. Fetching the task record from database
        2. Updating status to RUNNING
        3. Sending heartbeat
        4. Calling execute()
        5. Handling result (success/cancelled/failure)
        6. ACKing the task
        7. Clearing heartbeat

        Args:
            task_data: Parsed task data from queue
            task_json: Original JSON string for ACK

        Returns:
            True if task was processed, False if task not found
        """
        db_task_id = task_data.get("db_task_id")
        task_id = task_data.get("id")

        # Fetch task record
        task_record = await self._get_task_record(db_task_id)
        if not task_record:
            logger.warning("Task not found in database", db_task_id=db_task_id)
            await self.task_manager.ack_task(task_json)
            return False

        try:
            # Update status to RUNNING
            await self._update_status(task_record, TaskStatus.RUNNING)

            # Send initial heartbeat
            await self.context.orphan_recovery.send_heartbeat(task_id)

            # Execute the task
            result = await self.execute(task_data, task_record)

            # Handle skipped result (e.g., lock unavailable) - check retry limit
            if result.skipped:
                retry_count = task_data.get("retry_count", 0)

                if retry_count >= MAX_RETRIES:
                    # Exceeded max retries - move to DLQ
                    logger.warning(
                        "Task exceeded max retries, moving to DLQ",
                        db_task_id=db_task_id,
                        retry_count=retry_count,
                        max_retries=MAX_RETRIES,
                        reason=result.data.get("reason", "unknown"),
                    )
                    await self.task_manager.nack_task(task_json, retry=False)
                else:
                    # Still within retry limit - retry
                    logger.info(
                        "Task skipped, will retry",
                        db_task_id=db_task_id,
                        retry_count=retry_count,
                        reason=result.data.get("reason", "unknown"),
                    )
                    await self.task_manager.nack_task(task_json, retry=True)

                await self.context.orphan_recovery.clear_heartbeat(task_id)
                return True

            # Handle result
            if result.cancelled:
                await self._complete_cancelled(task_record, result)
            elif result.success:
                await self._complete_success(task_record, result)
            else:
                await self._complete_failure(task_record, result)

            # ACK task
            await self.task_manager.ack_task(task_json)
            await self.context.orphan_recovery.clear_heartbeat(task_id)
            return True

        except Exception as e:
            logger.error(
                "Task failed with error",
                db_task_id=db_task_id,
                task_id=task_id,
                error=str(e),
            )
            await self._handle_failure(task_record, task_json, e)
            return False

    async def _get_task_record(self, task_id: int) -> Optional[Task]:
        """Fetch task record from database."""
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def _update_status(self, task: Task, status: TaskStatus) -> None:
        """Update task status in database."""
        task.status = status
        if status == TaskStatus.RUNNING:
            task.started_at = utc_now()
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

    async def _complete_success(self, task: Task, result: TaskResult) -> None:
        """Mark task as completed successfully."""
        task.status = TaskStatus.COMPLETED
        task.completed_at = utc_now()
        task.result = result.to_json()
        self.session.add(task)
        await self.session.commit()

    async def _complete_cancelled(self, task: Task, result: TaskResult) -> None:
        """Mark task as cancelled."""
        task.status = TaskStatus.CANCELLED
        task.completed_at = utc_now()
        task.result = result.to_json()
        self.session.add(task)
        await self.session.commit()

    async def _complete_failure(self, task: Task, result: TaskResult) -> None:
        """Mark task as failed from TaskResult."""
        task.status = TaskStatus.FAILED
        task.completed_at = utc_now()
        task.result = json.dumps({"error": result.error, **result.data})
        self.session.add(task)
        await self.session.commit()

    async def _handle_failure(
        self, task: Task, task_json: str, error: Exception
    ) -> None:
        """
        Handle task failure from exception.

        Updates database status to FAILED and ACKs the task.
        Handles cases where session is in rolled back state (e.g., IntegrityError).
        """
        # First rollback the session (it may be in rolled back state from IntegrityError)
        try:
            await self.session.rollback()
        except Exception:
            pass  # Ignore rollback errors

        try:
            # Try to update DB status
            task.status = TaskStatus.FAILED
            task.completed_at = utc_now()
            task.result = json.dumps({"error": str(error)})
            self.session.add(task)
            await self.session.commit()
        except Exception as db_error:
            # DB update failed, log but continue to ACK
            logger.error(
                "Failed to update task status in DB",
                error=str(db_error),
                original_error=str(error),
            )
            try:
                await self.session.rollback()
            except Exception:
                pass

        # Always ACK the task (regardless of DB update success)
        await self.task_manager.ack_task(task_json)
