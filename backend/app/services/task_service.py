from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from redis.asyncio import Redis
from typing import Optional, List

from app.models.asset import Asset
from app.models.task import Task, TaskType, TaskStatus
from app.models.target import Target
from app.core.queue import TaskManager
from app.core.exceptions import TargetNotFoundError, DuplicateScanError
from app.core.url_validator import validate_url


class TaskService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.redis = redis
        self.task_manager = TaskManager(redis)

    async def create_scan_task(self, project_id: int, target_id: int) -> Task:
        """
        Creates a new scan task in DB and enqueues it to Redis.

        Validation order:
        1. Target exists → TargetNotFoundError (404)
        2. URL is safe → UnsafeUrlError (400)
        3. No duplicate scan → DuplicateScanError (409)

        Args:
            project_id: Project ID
            target_id: Target ID

        Returns:
            Created Task

        Raises:
            TargetNotFoundError: If target doesn't exist
            UnsafeUrlError: If target URL is unsafe (localhost, private IP, etc.)
            DuplicateScanError: If a scan is already in progress for this target
        """
        # 1. Fetch Target and validate existence
        target = await self.session.get(Target, target_id)
        if not target:
            raise TargetNotFoundError(target_id=target_id)

        # 2. Validate URL safety
        validate_url(target.url)

        # 3. Check for duplicate scans (PENDING or RUNNING)
        existing_task = await self._get_active_task_for_target(target_id)
        if existing_task:
            raise DuplicateScanError(
                target_id=target_id,
                existing_task_id=existing_task.id,
            )

        # 4. Create Task Record in DB
        task = Task(
            project_id=project_id,
            target_id=target_id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        # 5. Enqueue to Redis
        await self.task_manager.enqueue_crawl_task(
            project_id, target_id, db_task_id=task.id
        )

        return task

    async def _get_active_task_for_target(self, target_id: int) -> Optional[Task]:
        """
        Check if there's an active (PENDING or RUNNING) task for the target.

        Args:
            target_id: Target ID

        Returns:
            Active Task if exists, None otherwise
        """
        statement = (
            select(Task)
            .where(Task.target_id == target_id)
            .where(Task.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]))  # type: ignore[union-attr]
            .limit(1)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_task(self, task_id: int) -> Optional[Task]:
        return await self.session.get(Task, task_id)

    async def get_task_assets(self, task_id: int) -> List[Asset]:
        """Get assets discovered by a task via AssetDiscovery join."""
        from app.models.asset import AssetDiscovery

        statement = (
            select(Asset)
            .join(AssetDiscovery, Asset.id == AssetDiscovery.asset_id)
            .where(AssetDiscovery.task_id == task_id)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def cancel_task(self, task_id: int) -> Task:
        """
        Cancel a running or pending task.

        Args:
            task_id: Database Task ID

        Returns:
            Updated Task object with CANCELLED status

        Raises:
            ValueError: If task not found or already completed/failed/cancelled
        """
        from datetime import datetime, timezone

        # 1. Fetch task
        task = await self.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # 2. Validate state
        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            raise ValueError(
                f"Cannot cancel task in {task.status} state. "
                f"Only PENDING or RUNNING tasks can be cancelled."
            )

        # 3. Set Redis cancellation flag (Worker will check this)
        cancel_key = f"task:{task_id}:cancel"
        await self.redis.set(cancel_key, "1", ex=3600)  # 1-hour TTL

        # 4. Update DB status
        task.status = TaskStatus.CANCELLED
        if not task.completed_at:
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def get_latest_task_for_target(self, target_id: int) -> Optional[Task]:
        """
        Get the most recent task for a target.

        Args:
            target_id: Target ID

        Returns:
            Latest Task (sorted by created_at DESC) or None if no tasks exist
        """
        statement = (
            select(Task)
            .where(Task.target_id == target_id)
            .order_by(Task.created_at.desc())
            .limit(1)
        )

        result = await self.session.exec(statement)
        return result.first()
