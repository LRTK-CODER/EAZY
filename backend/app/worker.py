"""
DEPRECATED: This module is deprecated and will be removed in a future version.

Use the new workers package instead:
    from app.workers import run_worker
    asyncio.run(run_worker())

For custom workers:
    from app.workers import BaseWorker, WorkerContext, TaskResult
    from app.workers import WORKER_REGISTRY, register_worker, create_worker
"""
import asyncio
import json
import logging
import warnings
from redis.asyncio import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.queue import TaskManager
from app.models.project import Project  # Import all models for SQLAlchemy metadata
from app.models.target import Target
from app.models.task import Task, TaskStatus, TaskType
from app.core.utils import utc_now
from app.models.asset import Asset, AssetDiscovery, AssetType, AssetSource
from app.services.crawler_service import CrawlerService
from app.services.asset_service import AssetService

# Emit deprecation warning on import
warnings.warn(
    "app.worker is deprecated and will be removed in a future version. "
    "Use app.workers instead: from app.workers import run_worker",
    DeprecationWarning,
    stacklevel=2,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_cancellation(task_manager: TaskManager, task_id: int) -> bool:
    """
    Check if task has been cancelled via Redis flag.

    Args:
        task_manager: TaskManager instance
        task_id: Database Task ID

    Returns:
        True if task should be cancelled, False otherwise
    """
    cancel_key = f"task:{task_id}:cancel"
    cancel_flag = await task_manager.redis.get(cancel_key)
    return cancel_flag is not None

async def process_task(task_id: int, session: AsyncSession, task_manager: TaskManager | None = None) -> None:
    """
    Process a single task by ID (for testing).

    Args:
        task_id: Database Task ID
        session: AsyncSession instance
        task_manager: TaskManager instance (optional, will create if None)
    """
    # Create TaskManager if not provided
    if task_manager is None:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        task_manager = TaskManager(redis)

    # Fetch the Task record
    stmt = select(Task).where(Task.id == task_id)
    result = await session.exec(stmt)
    task_record = result.first()

    if not task_record:
        raise ValueError(f"Task {task_id} not found")

    # Update status to RUNNING
    task_record.status = TaskStatus.RUNNING
    task_record.started_at = utc_now()
    session.add(task_record)
    await session.commit()

    # Execute the task
    try:
        if task_record.type == TaskType.CRAWL:
            target = await session.get(Target, task_record.target_id)
            if not target:
                raise ValueError(f"Target {task_record.target_id} not found")

            # Type assertion: target_id is guaranteed non-None after successful get
            assert task_record.target_id is not None

            crawler = CrawlerService()
            links, http_data = await crawler.crawl(target.url)

            # Save Assets (using Context Manager for batch processing)
            saved_count = 0
            async with AssetService(session) as asset_service:
                last_check_time = asyncio.get_event_loop().time()
                for link in links:
                    # Check cancellation every 5 seconds
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_check_time >= 5.0:
                        is_cancelled = await check_cancellation(task_manager, task_id)
                        if is_cancelled:
                            logger.info(f"Task {task_id} cancelled by user")

                            # Flush pending assets before cancellation
                            await asset_service.flush()

                            # Update status to CANCELLED
                            task_record.status = TaskStatus.CANCELLED
                            task_record.completed_at = utc_now()
                            task_record.result = json.dumps({
                                "cancelled": True,
                                "processed_links": saved_count,
                                "total_links": len(links),
                                "message": "Task cancelled by user"
                            })
                            session.add(task_record)
                            await session.commit()

                            # Clean up Redis flag
                            cancel_key = f"task:{task_id}:cancel"
                            await task_manager.redis.delete(cancel_key)

                            return

                        last_check_time = current_time

                    # Extract HTTP data for this link
                    link_http_data = http_data.get(link, {})
                    request_data = link_http_data.get("request")
                    response_data = link_http_data.get("response")
                    parameters_data = link_http_data.get("parameters")

                    # Get HTTP method from request data
                    http_method = request_data.get("method", "GET") if request_data else "GET"

                    await asset_service.process_asset(
                        target_id=task_record.target_id,
                        task_id=task_id,
                        url=link,
                        method=http_method,
                        type=AssetType.URL,
                        source=AssetSource.HTML,
                        request_spec=request_data,
                        response_spec=response_data,
                        parameters=parameters_data
                    )
                    saved_count += 1

            # Update status to COMPLETED (after Context Manager exits and flushes)
            task_record.status = TaskStatus.COMPLETED
            task_record.completed_at = utc_now()
            task_record.result = json.dumps({"found_links": len(links), "saved_assets": saved_count})
            session.add(task_record)
            await session.commit()

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        task_record.status = TaskStatus.FAILED
        task_record.completed_at = utc_now()
        task_record.result = json.dumps({"error": str(e)})
        session.add(task_record)
        await session.commit()
        raise

async def process_one_task(session: AsyncSession, task_manager: TaskManager) -> bool:
    """
    Process a single task from the queue.
    Returns True if a task was processed, False if queue was empty.
    """
    # 1. Dequeue (returns tuple: task_data, task_json)
    result = await task_manager.dequeue_task()
    if not result:
        return False
    task_data, task_json = result
    
    logger.info(f"Processing task: {task_data}")
    
    db_task_id = task_data.get("db_task_id")
    target_id = task_data.get("target_id")
    task_type = task_data.get("type")
    
    if not db_task_id or not target_id:
        logger.error("Invalid task data: missing db_task_id or target_id")
        # ACK invalid task to prevent stuck tasks
        await task_manager.ack_task(task_json)
        return True  # Consumed but invalid
        
    # 2. Update Status -> RUNNING
    # We need to fetch the Task record first
    logger.info(f"Querying Task with ID: {db_task_id} (Type: {type(db_task_id)})")
    stmt = select(Task).where(Task.id == db_task_id)
    result = await session.exec(stmt)
    task_record = result.first()
    
    if not task_record:
        logger.error(f"Task record {db_task_id} not found in DB. Session hash: {hash(session)}")
        # Debug: list all tasks
        all_tasks = await session.exec(select(Task))
        logger.error(f"All Tasks in DB: {all_tasks.all()}")
        # ACK task not found in DB to prevent stuck tasks
        await task_manager.ack_task(task_json)
        return True
        
    task_record.status = TaskStatus.RUNNING
    task_record.started_at = utc_now()
    session.add(task_record)
    await session.commit()
    
    # 3. Execute Task (CRAWL)
    try:
        if task_type == TaskType.CRAWL:
            # We need the Target URL
            target = await session.get(Target, target_id)
            if not target:
                raise ValueError(f"Target {target_id} not found")
                
            crawler = CrawlerService()
            # In a real worker, we might want to launch the browser once and reuse,
            # but for safety let's do per-task for now or let service handle it.
            # CrawlerService currently launches browser in crawl_page.

            # Extract links and HTTP data
            links, http_data = await crawler.crawl(target.url)
            
            # 4. Save Assets (using Context Manager for batch processing)
            saved_count = 0
            async with AssetService(session) as asset_service:
                last_check_time = asyncio.get_event_loop().time()
                for index, link in enumerate(links, start=1):
                    # Check cancellation every 5 seconds
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_check_time >= 5.0:
                        is_cancelled = await check_cancellation(task_manager, db_task_id)
                        if is_cancelled:
                            logger.info(f"Task {db_task_id} cancelled by user at link {index}/{len(links)}")

                            # Flush pending assets before cancellation
                            await asset_service.flush()

                            # Update status to CANCELLED
                            task_record.status = TaskStatus.CANCELLED
                            task_record.completed_at = utc_now()
                            task_record.result = json.dumps({
                                "cancelled": True,
                                "processed_links": saved_count,
                                "total_links": len(links),
                                "message": "Task cancelled by user"
                            })
                            session.add(task_record)
                            await session.commit()

                            # Clean up Redis flag
                            cancel_key = f"task:{db_task_id}:cancel"
                            await task_manager.redis.delete(cancel_key)

                            # ACK: Remove from processing queue
                            await task_manager.ack_task(task_json)

                            return True

                        last_check_time = current_time

                    # Extract HTTP data for this link (if available)
                    link_http_data = http_data.get(link, {})
                    request_data = link_http_data.get("request")
                    response_data = link_http_data.get("response")
                    parameters_data = link_http_data.get("parameters")

                    # Get HTTP method from request data, default to GET
                    http_method = request_data.get("method", "GET") if request_data else "GET"

                    await asset_service.process_asset(
                        target_id=target_id,
                        task_id=db_task_id,
                        url=link,
                        method=http_method,
                        type=AssetType.URL,
                        source=AssetSource.HTML,
                        request_spec=request_data,
                        response_spec=response_data,
                        parameters=parameters_data
                    )
                    saved_count += 1

            # 5. Update Status -> COMPLETED (after Context Manager exits and flushes)
            task_record.status = TaskStatus.COMPLETED
            task_record.completed_at = utc_now()
            task_record.result = json.dumps({"found_links": len(links), "saved_assets": saved_count})
            session.add(task_record)
            await session.commit()

            # 6. ACK: Remove from processing queue
            await task_manager.ack_task(task_json)

        else:
            logger.warning(f"Unknown task type: {task_type}")
            # ACK unknown task types to prevent stuck tasks
            await task_manager.ack_task(task_json)

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        task_record.status = TaskStatus.FAILED
        task_record.completed_at = utc_now()
        task_record.result = json.dumps({"error": str(e)})
        session.add(task_record)
        await session.commit()
        # ACK failed tasks (they're marked as FAILED in DB)
        await task_manager.ack_task(task_json)
        raise

    return True

async def run_worker() -> None:
    """
    Main loop for the worker.
    """
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    task_manager = TaskManager(redis)
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    logger.info("Worker started. Waiting for tasks...")
    
    try:
        while True:
            async with async_session() as session:
                await process_one_task(session, task_manager)
                # BLPOP handles blocking, no sleep needed
    except KeyboardInterrupt:
        logger.info("Worker stopped")
    finally:
        await redis.aclose()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_worker())
