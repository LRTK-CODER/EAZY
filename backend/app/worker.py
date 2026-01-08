import asyncio
import logging
from redis.asyncio import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.queue import TaskManager
from app.models.project import Project  # Import all models for SQLAlchemy metadata
from app.models.target import Target
from app.models.task import Task, TaskStatus, TaskType, utc_now
from app.models.asset import Asset, AssetDiscovery, AssetType, AssetSource
from app.services.crawler_service import CrawlerService
from app.services.asset_service import AssetService

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

async def process_one_task(session: AsyncSession, task_manager: TaskManager) -> bool:
    """
    Process a single task from the queue.
    Returns True if a task was processed, False if queue was empty.
    """
    # 1. Dequeue
    task_data = await task_manager.dequeue_task()
    if not task_data:
        return False
    
    logger.info(f"Processing task: {task_data}")
    
    db_task_id = task_data.get("db_task_id")
    target_id = task_data.get("target_id")
    task_type = task_data.get("type")
    
    if not db_task_id or not target_id:
        logger.error("Invalid task data: missing db_task_id or target_id")
        return True # Consumed but invalid
        
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
            
            # Extract links
            links = await crawler.crawl(target.url)
            
            # 4. Save Assets
            asset_service = AssetService(session)
            saved_count = 0
            for index, link in enumerate(links, start=1):
                # Check cancellation every 10 links
                if index % 10 == 0:
                    is_cancelled = await check_cancellation(task_manager, db_task_id)
                    if is_cancelled:
                        logger.info(f"Task {db_task_id} cancelled by user at link {index}/{len(links)}")

                        # Update status to CANCELLED
                        import json
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

                        return True

                await asset_service.process_asset(
                    target_id=target_id,
                    task_id=db_task_id,
                    url=link,
                    method="GET", # Crawled links are usually GET
                    type=AssetType.URL,
                    source=AssetSource.HTML
                )
                saved_count += 1
            
            # 5. Update Status -> COMPLETED
            import json
            task_record.status = TaskStatus.COMPLETED
            task_record.completed_at = utc_now()
            task_record.result = json.dumps({"found_links": len(links), "saved_assets": saved_count})
            session.add(task_record)
            await session.commit()
            
        else:
            logger.warning(f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        import json
        task_record.status = TaskStatus.FAILED
        task_record.completed_at = utc_now()
        task_record.result = json.dumps({"error": str(e)})
        session.add(task_record)
        await session.commit()
        
    return True

async def run_worker():
    """
    Main loop for the worker.
    """
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    task_manager = TaskManager(redis)
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    logger.info("Worker started. Waiting for tasks...")
    
    try:
        while True:
            async with async_session() as session:
                processed = await process_one_task(session, task_manager)
                if not processed:
                    await asyncio.sleep(1) # Sleep if queue empty
    except KeyboardInterrupt:
        logger.info("Worker stopped")
    finally:
        await redis.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_worker())
