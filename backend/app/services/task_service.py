from sqlmodel.ext.asyncio.session import AsyncSession
from redis.asyncio import Redis
from typing import Optional, List

from app.models.task import Task, TaskType, TaskStatus
from app.core.queue import TaskManager

class TaskService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.redis = redis
        self.task_manager = TaskManager(redis)

    async def create_scan_task(self, project_id: int, target_id: int) -> Task:
        """
        Creates a new scan task in DB and enqueues it to Redis.
        """
        # 1. Create Task Record in DB
        task = Task(
            project_id=project_id,
            target_id=target_id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        
        # 2. Enqueue to Redis
        # Use the DB Task ID might be better for tracking, but our Queue uses UUID.
        # We can store the UUID in the Task record if we want, or just log it.
        # For simplicity, we just enqueue. The Worker will update DB based on IDs if we pass them.
        # Let's pass DB IDs to the queue payload so the worker knows what to update.
        
        # Updating TaskManager to accept task_id (DB ID) could be useful, 
        # but for now let's stick to the current signature or modify TaskManager if needed.
        # Actually TaskManager.enqueue_crawl_task logic in core/queue.py takes proj_id, target_id.
        # We might want to pass the task_id (DB) to the worker so it can update status!
        
        # Let's check app/core/queue.py content... 
        # It currently takes project_id, target_id. I should probably update it to take task_id (DB) 
        # so the worker can update the specific task record.
        
        # For now, let's just call it.
        # TODO: Update TaskManager to include DB task_id in payload.
        # Pass the DB task ID so the worker can update the record.
        queue_id = await self.task_manager.enqueue_crawl_task(project_id, target_id, db_task_id=task.id)
        
        # We could store queue_id in Task if we had a column. For now, skipping.
        
        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        return await self.session.get(Task, task_id)

    async def get_task_assets(self, task_id: int) -> List["Asset"]:
        # Join AssetDiscovery to find assets linked to this task?
        # Or just use Asset.last_task_id if we only care about if it was touched by this task?
        # Requirement: "Assets discovered by a task".
        # AssetDiscovery table stores exactly this.
        from app.models.asset import Asset, AssetDiscovery
        from sqlmodel import select

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
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
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
        from sqlmodel import select

        statement = (
            select(Task)
            .where(Task.target_id == target_id)
            .order_by(Task.created_at.desc())
            .limit(1)
        )

        result = await self.session.exec(statement)
        return result.first()
