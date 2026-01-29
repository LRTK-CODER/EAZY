"""CrawlWorker - Thin wrapper that delegates to CrawlOrchestrator."""

from typing import Any, Callable, Dict, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.application.context.pipeline_context import OrchestratorResult
from app.application.orchestrators.crawl_orchestrator import CrawlOrchestrator
from app.application.stages import (
    AssetStage,
    CrawlStage,
    DiscoveryStage,
    GuardStage,
    LoadTargetStage,
    RecurseStage,
)
from app.core.constants import LOCK_PREFIX, LOCK_TTL
from app.core.exceptions import TargetNotFoundError
from app.core.lock import DistributedLock
from app.core.structured_logger import get_logger
from app.domain.services.data_transformer import DataTransformer
from app.domain.services.scope_checker import ScopeChecker
from app.domain.services.url_validator import UrlValidator
from app.infrastructure.adapters import (
    AssetRepositoryAdapter,
    CancellationAdapter,
    CrawlerAdapter,
    TaskQueueAdapter,
)
from app.models.target import Target
from app.models.task import Task, TaskType
from app.services.asset_service import AssetService
from app.services.crawl_manager import CrawlManager
from app.services.crawler_service import CrawlerService
from app.services.discovery import DiscoveryService, get_default_registry
from app.services.interfaces import ICrawler
from app.workers.base import BaseWorker, TaskResult, WorkerContext

logger = get_logger(__name__)


class CrawlWorker(BaseWorker):
    """Thin wrapper for crawl tasks - delegates to CrawlOrchestrator."""

    def __init__(
        self,
        context: WorkerContext,
        crawler_service: Optional[ICrawler] = None,
        asset_service_factory: Optional[Callable[[AsyncSession], AssetService]] = None,
        crawl_manager_factory: Optional[
            Callable[[AsyncSession, Any], CrawlManager]
        ] = None,
        discovery_service: Optional[DiscoveryService] = None,
    ):
        super().__init__(context)
        self.crawler = crawler_service or CrawlerService()
        self.asset_service_factory = asset_service_factory or (
            lambda s: AssetService(s)
        )
        self.crawl_manager_factory = crawl_manager_factory or (
            lambda s, r: CrawlManager(s, r)
        )
        self.discovery_service = discovery_service or DiscoveryService(
            registry=get_default_registry()
        )

    @property
    def task_type(self) -> TaskType:
        return TaskType.CRAWL

    async def execute(self, task_data: Dict[str, Any], task_record: Task) -> TaskResult:
        """Execute crawl task by delegating to CrawlOrchestrator."""
        target_id = task_data.get("target_id")
        db_task_id = task_data.get("db_task_id")

        # Pre-checks: target exists and URLs are safe
        target = await self.session.get(Target, target_id)
        if not target or not target_id:
            raise TargetNotFoundError(target_id=target_id or 0)

        url_validator = UrlValidator()
        if not url_validator.is_safe(target.url):
            logger.warning("Blocked unsafe URL", target_id=target_id, url=target.url)
            return TaskResult.create_skipped(
                {"reason": "unsafe_url", "target_id": target_id, "url": target.url}
            )

        if task_record.crawl_url and not url_validator.is_safe(task_record.crawl_url):
            logger.warning(
                "Blocked unsafe crawl URL",
                target_id=target_id,
                crawl_url=task_record.crawl_url,
            )
            return TaskResult.create_skipped(
                {"reason": "unsafe_crawl_url", "crawl_url": task_record.crawl_url}
            )

        # Acquire lock
        lock = DistributedLock(
            redis=self.task_manager.redis,
            name=f"task:{db_task_id}",
            ttl=LOCK_TTL,
            prefix=LOCK_PREFIX,
        )
        if not await lock.acquire():
            logger.warning("Could not acquire lock", db_task_id=db_task_id)
            return TaskResult.create_skipped(
                {"reason": "lock_unavailable", "db_task_id": db_task_id}
            )

        try:
            # Delegate to orchestrator
            stages, task_queue_adapter, asset_service = self._create_stages(target)
            cancellation_adapter = CancellationAdapter(self.task_manager.redis)
            orchestrator = CrawlOrchestrator(
                stages=stages, cancellation=cancellation_adapter
            )

            # Enter AssetService context for proper flushing
            async with asset_service:
                result = await orchestrator.execute(
                    task_record, target_id, session=self.session
                )

                # Flush task queue unless cancelled
                if not result.cancelled:
                    await task_queue_adapter.flush()
                # AssetService.flush() is called automatically on __aexit__

            # Clear cancel flag if cancelled
            if result.cancelled and task_record.id:
                await self._clear_cancel_flag(task_record.id)

            return self._to_task_result(result, task_record)
        finally:
            await lock.release()

    def _create_stages(
        self, target: Target
    ) -> tuple[list[Any], TaskQueueAdapter, AssetService]:
        """Create pipeline stages with adapters."""
        data_transformer = DataTransformer()
        asset_service = self.asset_service_factory(self.session)
        crawl_manager = self.crawl_manager_factory(
            self.session, self.task_manager.redis
        )

        task_queue_adapter = TaskQueueAdapter(crawl_manager)
        url_validator = UrlValidator()
        scope_checker = ScopeChecker()

        stages = [
            LoadTargetStage(self.session),
            GuardStage(url_validator, scope_checker),
            CrawlStage(CrawlerAdapter(self.crawler)),
            DiscoveryStage(self.discovery_service, data_transformer),
            AssetStage(AssetRepositoryAdapter(asset_service, target, data_transformer)),
            RecurseStage(task_queue_adapter, scope_checker),
        ]
        return stages, task_queue_adapter, asset_service

    def _to_task_result(
        self, result: OrchestratorResult, task_record: Task
    ) -> TaskResult:
        """Convert OrchestratorResult to TaskResult."""
        data = {
            "saved_assets": result.saved_assets,
            "child_tasks_spawned": result.child_tasks_spawned,
            "found_links": result.found_links,
            "discovered_assets": result.discovered_assets,
        }

        # Check for cancellation FIRST (via dedicated flag)
        if result.cancelled:
            logger.info("Task cancelled", task_id=task_record.id)
            return TaskResult.create_cancelled(
                {**data, "cancelled": True, "message": "Task cancelled by user"}
            )

        if result.errors:
            # Check for cancellation in errors (fallback)
            for stage, error_msg in result.errors:
                if "cancel" in error_msg.lower():
                    logger.info("Task cancelled", task_id=task_record.id)
                    return TaskResult.create_cancelled(
                        {**data, "cancelled": True, "message": "Task cancelled by user"}
                    )

            # Otherwise it's a failure
            error_msg = "; ".join([f"{stage}: {err}" for stage, err in result.errors])
            logger.error("Task failed", task_id=task_record.id, errors=error_msg)
            return TaskResult.create_failure(error_msg, data)

        return TaskResult.create_success(data)

    async def _clear_cancel_flag(self, task_id: int) -> None:
        """Clear Redis cancel flag after handling cancellation."""
        cancel_key = f"task:{task_id}:cancel"
        await self.task_manager.redis.delete(cancel_key)
