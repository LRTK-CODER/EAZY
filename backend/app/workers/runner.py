"""
Worker Runner for EAZY worker infrastructure.

Phase 3: Architecture Improvement

Provides the main worker loop and utilities for processing tasks.
"""

import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.queue import TaskManager
from app.core.dlq import DLQManager
from app.core.recovery import OrphanRecovery
from app.core.structured_logger import get_logger
from app.workers.base import WorkerContext

# Import all models to register them with SQLAlchemy metadata
# This is required for foreign key relationships to work correctly
import app.models  # noqa: F401
from app.workers.registry import get_worker_class, create_worker


logger = get_logger(__name__)


def create_worker_context(
    session: AsyncSession,
    redis: Redis,
) -> WorkerContext:
    """
    Create WorkerContext with all dependencies.

    Args:
        session: Database session
        redis: Redis client

    Returns:
        Configured WorkerContext
    """
    task_manager = TaskManager(redis)
    dlq_manager = DLQManager(redis)
    orphan_recovery = OrphanRecovery(redis)

    return WorkerContext(
        session=session,
        task_manager=task_manager,
        dlq_manager=dlq_manager,
        orphan_recovery=orphan_recovery,
    )


async def process_one_task(context: WorkerContext) -> bool:
    """
    Process a single task from the queue.

    Args:
        context: WorkerContext with all dependencies

    Returns:
        True if a task was processed, False if queue was empty
    """
    task_manager = context.task_manager

    # Dequeue task
    result = await task_manager.dequeue_task()
    if not result:
        return False

    task_data, task_json = result
    db_task_id = task_data.get("db_task_id")
    target_id = task_data.get("target_id")
    task_type = task_data.get("type", "crawl")
    task_id = task_data.get("id")

    # Bind context for this task
    log = logger.bind(task_id=task_id, db_task_id=db_task_id, target_id=target_id)
    log.info("Processing task", task_type=task_type)

    # Validate task data
    if not db_task_id or not target_id:
        log.error("Invalid task data: missing db_task_id or target_id")
        await task_manager.ack_task(task_json)
        return True

    # Get worker class
    worker_class = get_worker_class(task_type)
    if worker_class is None:
        log.warning("Unknown task type", task_type=task_type)
        await task_manager.ack_task(task_json)
        return True

    # Create and run worker
    try:
        worker = create_worker(task_type, context)
        await worker.process(task_data, task_json)
    except Exception as e:
        log.error("Task processing failed", error=str(e))
        # Task is already ACKed in worker.process() on failure

    return True


async def run_worker() -> None:
    """
    Main loop for the worker.

    Creates database connection, Redis connection, and processes tasks
    in an infinite loop until interrupted.
    """
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    logger.info("Worker started. Waiting for tasks...")

    try:
        while True:
            async with async_session() as session:
                context = create_worker_context(session, redis)
                await process_one_task(context)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    finally:
        await redis.aclose()
        await engine.dispose()
        logger.info("Worker cleanup completed")


if __name__ == "__main__":
    asyncio.run(run_worker())
