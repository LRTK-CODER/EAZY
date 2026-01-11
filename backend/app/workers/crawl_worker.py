"""
CrawlWorker for EAZY crawl tasks.

Phase 3: Architecture Improvement
Phase 4: Scalability - Distributed Lock Integration
Phase 4 Day 5: SSRF Prevention
"""

import asyncio
import ipaddress
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

from sqlmodel.ext.asyncio.session import AsyncSession

from app.workers.base import BaseWorker, WorkerContext, TaskResult
from app.models.task import Task, TaskType
from app.models.target import Target
from app.models.asset import AssetType, AssetSource
from app.services.crawler_service import CrawlerService
from app.services.asset_service import AssetService
from app.core.lock import DistributedLock
from app.core.structured_logger import get_logger


logger = get_logger(__name__)

# Cancellation check interval in seconds
CANCELLATION_CHECK_INTERVAL = 5.0

# Lock configuration (matching OrphanRecovery threshold)
LOCK_TTL = 600  # 10 minutes
LOCK_PREFIX = "eazy:lock:"

# SSRF Prevention - Blocked schemes and hosts
BLOCKED_SCHEMES = {"file", "gopher", "ftp", "data"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


def is_safe_url(url: Optional[str]) -> bool:
    """
    Validate URL for SSRF prevention.

    Blocks:
    - Internal/private IP addresses (10.x, 172.16-31.x, 192.168.x)
    - Loopback addresses (localhost, 127.0.0.1, ::1)
    - AWS metadata endpoint (169.254.169.254)
    - Dangerous schemes (file://, gopher://, ftp://)

    Args:
        url: URL to validate

    Returns:
        True if URL is safe to crawl, False otherwise
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Must have a scheme
        if not parsed.scheme:
            return False

        # Block dangerous schemes
        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            return False

        # Must have a hostname
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block known dangerous hosts
        if hostname.lower() in BLOCKED_HOSTS:
            return False

        # Check if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # Block private, reserved, loopback IPs
            if ip.is_private or ip.is_reserved or ip.is_loopback:
                return False
            # Block link-local addresses (169.254.x.x - AWS metadata)
            if ip.is_link_local:
                return False
        except ValueError:
            # hostname is a domain name, not an IP - that's fine
            pass

        return True
    except Exception:
        return False


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
        self.asset_service_factory = asset_service_factory or (
            lambda s: AssetService(s)
        )

    @property
    def task_type(self) -> TaskType:
        """Return the task type this worker handles."""
        return TaskType.CRAWL

    async def execute(self, task_data: Dict[str, Any], task_record: Task) -> TaskResult:
        """
        Execute crawl task with distributed lock.

        Args:
            task_data: Task data from queue containing target_id, db_task_id
            task_record: Task record from database

        Returns:
            TaskResult indicating success, failure, cancellation, or skipped
        """
        target_id = task_data.get("target_id")
        db_task_id = task_data.get("db_task_id")

        # Fetch target
        target = await self.session.get(Target, target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")

        # SSRF Prevention: Validate URL before crawling
        if not is_safe_url(target.url):
            logger.warning("Blocked unsafe URL", target_id=target_id, url=target.url)
            return TaskResult.create_skipped(
                {
                    "reason": "unsafe_url",
                    "target_id": target_id,
                    "url": target.url,
                    "message": f"URL {target.url} blocked for security reasons",
                }
            )

        # Create distributed lock for target
        lock = DistributedLock(
            redis=self.task_manager.redis,
            name=f"target:{target_id}",
            ttl=LOCK_TTL,
            prefix=LOCK_PREFIX,
        )

        # Try to acquire lock
        if not await lock.acquire():
            logger.warning(
                "Could not acquire lock for target, another worker is processing",
                target_id=target_id,
            )
            return TaskResult.create_skipped(
                {
                    "reason": "lock_unavailable",
                    "target_id": target_id,
                    "message": f"Target {target_id} is locked by another worker",
                }
            )

        try:
            # Crawl with lock held
            return await self._execute_with_lock(target, target_id, db_task_id)
        finally:
            # Always release lock
            await lock.release()

    async def _execute_with_lock(
        self,
        target: Target,
        target_id: int,
        db_task_id: int,
    ) -> TaskResult:
        """Execute crawl task while holding the lock."""
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
                        return TaskResult.create_cancelled(
                            {
                                "cancelled": True,
                                "processed_links": saved_count,
                                "total_links": len(links),
                                "message": "Task cancelled by user",
                            }
                        )
                    last_check_time = current_time

                # Extract HTTP data
                link_http_data = http_data.get(link, {})
                request_data = link_http_data.get("request")
                response_data = link_http_data.get("response")
                parameters_data = link_http_data.get("parameters")

                http_method = (
                    request_data.get("method", "GET") if request_data else "GET"
                )

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

        return TaskResult.create_success(
            {
                "found_links": len(links),
                "saved_assets": saved_count,
            }
        )

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
