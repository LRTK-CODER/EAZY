"""
CrawlWorker for EAZY crawl tasks.

Phase 3: Architecture Improvement
"""
import asyncio
from typing import Any, Callable, Dict, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.workers.base import BaseWorker, WorkerContext, TaskResult
from app.models.task import Task, TaskType
from app.models.target import Target
from app.models.asset import AssetType, AssetSource
from app.services.crawler_service import CrawlerService
from app.services.asset_service import AssetService


# Cancellation check interval in seconds
CANCELLATION_CHECK_INTERVAL = 5.0


class CrawlWorker(BaseWorker):
    """
    Worker for crawl tasks.

    Handles web crawling tasks by:
    1. Fetching target URL from database
    2. Crawling the target using CrawlerService
    3. Saving discovered assets using AssetService
    4. Supporting cancellation via Redis flag
    """

    def __init__(
        self,
        context: WorkerContext,
        crawler_service: Optional[CrawlerService] = None,
        asset_service_factory: Optional[Callable[[AsyncSession], AssetService]] = None,
    ):
        """
        Initialize CrawlWorker with optional dependency injection.

        Args:
            context: WorkerContext with shared dependencies
            crawler_service: Optional CrawlerService instance (for testing)
            asset_service_factory: Optional factory for AssetService (for testing)
        """
        super().__init__(context)
        self.crawler = crawler_service or CrawlerService()
        self.asset_service_factory = asset_service_factory or (lambda s: AssetService(s))

    @property
    def task_type(self) -> TaskType:
        """Return the task type this worker handles."""
        return TaskType.CRAWL

    async def execute(self, task_data: Dict[str, Any], task_record: Task) -> TaskResult:
        """
        Execute crawl task.

        Args:
            task_data: Task data from queue containing target_id, db_task_id
            task_record: Task record from database

        Returns:
            TaskResult indicating success, failure, or cancellation
        """
        target_id = task_data.get("target_id")
        db_task_id = task_data.get("db_task_id")

        # Fetch target
        target = await self.session.get(Target, target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")

        # Crawl
        links, http_data = await self.crawler.crawl(target.url)

        # Save assets
        saved_count = 0
        async with self.asset_service_factory(self.session) as asset_service:
            last_check_time = asyncio.get_event_loop().time()
            check_counter = 0
            CHECK_INTERVAL_ITEMS = 10  # Check every N items for faster response

            for link in links:
                check_counter += 1
                # Check cancellation periodically (by time or by item count)
                current_time = asyncio.get_event_loop().time()
                should_check = (
                    current_time - last_check_time >= CANCELLATION_CHECK_INTERVAL
                    or check_counter % CHECK_INTERVAL_ITEMS == 0
                )
                if should_check:
                    if await self._check_cancellation(db_task_id):
                        await asset_service.flush()
                        await self._clear_cancel_flag(db_task_id)
                        return TaskResult.create_cancelled({
                            "cancelled": True,
                            "processed_links": saved_count,
                            "total_links": len(links),
                            "message": "Task cancelled by user",
                        })
                    last_check_time = current_time

                # Extract HTTP data
                link_http_data = http_data.get(link, {})
                request_data = link_http_data.get("request")
                response_data = link_http_data.get("response")
                parameters_data = link_http_data.get("parameters")

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
                    parameters=parameters_data,
                )
                saved_count += 1

        return TaskResult.create_success({
            "found_links": len(links),
            "saved_assets": saved_count,
        })

    async def _check_cancellation(self, task_id: int) -> bool:
        """
        Check if task has been cancelled via Redis flag.

        Args:
            task_id: Database task ID

        Returns:
            True if cancel flag is set
        """
        cancel_key = f"task:{task_id}:cancel"
        cancel_flag = await self.task_manager.redis.get(cancel_key)
        return cancel_flag is not None

    async def _clear_cancel_flag(self, task_id: int) -> None:
        """
        Clear Redis cancel flag after handling.

        Args:
            task_id: Database task ID
        """
        cancel_key = f"task:{task_id}:cancel"
        await self.task_manager.redis.delete(cancel_key)
