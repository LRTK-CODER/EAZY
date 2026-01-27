"""
CrawlWorker for EAZY crawl tasks.

Phase 3: Architecture Improvement
Phase 4: Scalability - Distributed Lock Integration
Phase 4 Day 5: SSRF Prevention
"""

import asyncio
import ipaddress
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.constants import CANCELLATION_CHECK_INTERVAL, LOCK_PREFIX, LOCK_TTL
from app.core.exceptions import TargetNotFoundError
from app.core.lock import DistributedLock
from app.core.structured_logger import get_logger
from app.models.asset import AssetSource, AssetType
from app.models.target import Target
from app.models.task import Task, TaskType
from app.services.asset_service import AssetService
from app.services.crawl_manager import CrawlManager
from app.services.crawler_service import CrawlerService
from app.services.discovery import (
    DiscoveryContext,
    DiscoveryService,
    ScanProfile,
    get_default_registry,
)
from app.services.interfaces import ICrawler
from app.services.url_normalizer import normalize_url
from app.workers.base import BaseWorker, TaskResult, WorkerContext

logger = get_logger(__name__)


def _map_discovery_source(source: str) -> AssetSource:
    """Discovery source를 AssetSource로 매핑.

    Args:
        source: Discovery 모듈 이름

    Returns:
        대응하는 AssetSource
    """
    mapping = {
        "html_element_parser": AssetSource.HTML,
        "network_capturer": AssetSource.NETWORK,
        "js_analyzer_regex": AssetSource.JS,
        "js_analyzer_ast": AssetSource.JS,
        "config_discovery": AssetSource.HTML,
        "interaction_engine": AssetSource.DOM,
    }
    return mapping.get(source, AssetSource.HTML)


def _map_asset_type(asset_type: str) -> AssetType:
    """Discovery asset_type을 AssetType으로 매핑.

    Args:
        asset_type: Discovery에서 반환한 자산 유형

    Returns:
        대응하는 AssetType
    """
    if asset_type == "form":
        return AssetType.FORM
    elif asset_type in ("api_endpoint", "api_call", "xhr", "fetch"):
        return AssetType.XHR
    return AssetType.URL


def _transform_to_network_requests(http_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """http_data를 network_requests 형식으로 변환.

    Args:
        http_data: CrawlerService에서 반환한 HTTP 데이터

    Returns:
        NetworkCapturerModule이 필요로 하는 형식의 요청 목록
    """
    network_requests: List[Dict[str, Any]] = []
    for url, data in http_data.items():
        request = data.get("request")
        if not request:
            continue
        network_requests.append(
            {
                "url": url,
                "method": request.get("method", "GET"),
                "headers": request.get("headers", {}),
                "body": request.get("body"),
                "post_data": request.get("body"),  # NetworkCapturerModule 호환
                "resource_type": request.get("resource_type", ""),
            }
        )
    return network_requests


def _transform_to_network_responses(http_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """http_data를 network_responses 형식으로 변환.

    Args:
        http_data: CrawlerService에서 반환한 HTTP 데이터

    Returns:
        NetworkCapturerModule이 필요로 하는 형식의 응답 목록
    """
    network_responses: List[Dict[str, Any]] = []
    for url, data in http_data.items():
        response = data.get("response")
        if not response:
            continue
        network_responses.append(
            {
                "url": url,
                "status": response.get("status"),
                "headers": response.get("headers", {}),
                "body": response.get("body"),
            }
        )
    return network_responses


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
        crawler_service: Optional[ICrawler] = None,
        asset_service_factory: Optional[Callable[[AsyncSession], AssetService]] = None,
        crawl_manager_factory: Optional[
            Callable[[AsyncSession, Any], CrawlManager]
        ] = None,
        discovery_service: Optional[DiscoveryService] = None,
    ):
        """
        Initialize CrawlWorker with optional dependency injection.

        Args:
            context: WorkerContext with shared dependencies
            crawler_service: Optional ICrawler implementation (for testing)
            asset_service_factory: Optional factory for AssetService (for testing)
            crawl_manager_factory: Optional factory for CrawlManager (for testing)
            discovery_service: Optional DiscoveryService (for testing)
        """
        super().__init__(context)
        self.crawler = crawler_service or CrawlerService()
        self.asset_service_factory = asset_service_factory or (
            lambda s: AssetService(s)
        )
        self.crawl_manager_factory = crawl_manager_factory or (
            lambda s, r: CrawlManager(s, r)
        )
        # Discovery 서비스 초기화
        if discovery_service:
            self.discovery_service = discovery_service
        else:
            self.discovery_service = DiscoveryService(registry=get_default_registry())

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
            raise TargetNotFoundError(target_id=target_id)

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
            return await self._execute_with_lock(
                target, target_id, db_task_id, task_record
            )
        finally:
            # Always release lock
            await lock.release()

    async def _execute_with_lock(
        self,
        target: Target,
        target_id: int,
        db_task_id: int,
        task_record: Task,
    ) -> TaskResult:
        """Execute crawl task while holding the lock."""
        # crawl_url이 있으면 사용, 없으면 target.url (root task)
        crawl_target_url = task_record.crawl_url or target.url

        # SSRF Prevention: Validate crawl_target_url (defense-in-depth)
        # This catches unsafe URLs that might come from child tasks
        if not is_safe_url(crawl_target_url):
            logger.warning(
                "Blocked unsafe crawl URL",
                target_id=target_id,
                db_task_id=db_task_id,
                crawl_url=crawl_target_url,
            )
            return TaskResult.create_skipped(
                {
                    "reason": "unsafe_crawl_url",
                    "target_id": target_id,
                    "db_task_id": db_task_id,
                    "crawl_url": crawl_target_url,
                    "message": f"Crawl URL {crawl_target_url} blocked for security reasons",
                }
            )

        # Crawl
        links, http_data, js_contents = await self.crawler.crawl(crawl_target_url)

        # === Discovery 실행 ===
        # HTML content 추출 (리다이렉트 처리 포함)
        html_content = ""

        # 1. 먼저 crawl_target_url에서 찾기
        target_http_data = http_data.get(crawl_target_url, {})
        target_response_data = target_http_data.get("response", {})
        if target_response_data:
            body = target_response_data.get("body", "")
            if isinstance(body, str) and body:
                html_content = body

        # 2. crawl_target_url에 body가 없으면 (리다이렉트), 다른 URL에서 HTML 찾기
        if not html_content:
            for url, data in http_data.items():
                response_data = data.get("response", {})
                status = response_data.get("status")
                body = response_data.get("body", "")
                # 200 응답이고 HTML content인 경우
                if status == 200 and isinstance(body, str) and body:
                    # HTML인지 확인 (간단한 휴리스틱)
                    body_lower = body.lower()
                    if "<html" in body_lower or "<!doctype" in body_lower:
                        html_content = body
                        break

        # 데이터 변환 (Phase 3)
        network_requests = _transform_to_network_requests(http_data)
        network_responses = _transform_to_network_responses(http_data)

        # DiscoveryContext 생성 및 실행
        discovery_context = DiscoveryContext(
            target_url=crawl_target_url,
            profile=ScanProfile.STANDARD,
            http_client=None,  # 이미 크롤링 완료
            crawl_data={
                "html_content": html_content,
                "base_url": crawl_target_url,
                "http_data": http_data,
                "js_contents": js_contents,  # Phase 2: JS content 추가
                "network_requests": network_requests,  # Phase 3: 네트워크 요청 추가
                "network_responses": network_responses,  # Phase 3: 네트워크 응답 추가
            },
        )
        discovered_assets = await self.discovery_service.run(discovery_context)
        # === Discovery 실행 끝 ===

        # Save assets
        saved_count = 0
        discovery_saved_count = 0
        async with self.asset_service_factory(self.session) as asset_service:
            last_check_time = asyncio.get_event_loop().time()
            check_counter = 0
            CHECK_INTERVAL_ITEMS = 10  # Check every N items for faster response

            # 기존 links 저장 (Crawler에서 발견한 <a> 태그)
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

                # URL 정규화 (상대 URL → 절대 URL)
                normalized_link = str(normalize_url(link, base_url=crawl_target_url))

                # Extract HTTP data (원본 link로 조회)
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
                    url=normalized_link,  # 정규화된 URL 사용
                    method=http_method,
                    type=AssetType.URL,
                    source=AssetSource.HTML,
                    request_spec=request_data,
                    response_spec=response_data,
                    parameters=parameters_data,
                )
                saved_count += 1

            # === Discovery 결과 저장 ===
            for discovered in discovered_assets:
                # metadata에서 method 추출 (기본값 GET)
                method = discovered.metadata.get("method", "GET")
                # source 및 asset_type 매핑
                source = _map_discovery_source(discovered.source)
                asset_type = _map_asset_type(discovered.asset_type)

                await asset_service.process_asset(
                    target_id=target_id,
                    task_id=db_task_id,
                    url=discovered.url,
                    method=method,
                    type=asset_type,
                    source=source,
                )
                discovery_saved_count += 1
            # === Discovery 결과 저장 끝 ===

        # Spawn child tasks for recursive crawling
        child_tasks_spawned = 0
        current_depth = task_record.depth
        max_depth = task_record.max_depth

        if current_depth < max_depth and links:
            crawl_manager = self.crawl_manager_factory(
                self.session, self.task_manager.redis
            )
            child_tasks = await crawl_manager.spawn_child_tasks(
                parent_task_id=db_task_id,
                target_id=target_id,
                project_id=target.project_id,
                discovered_urls=links,
                current_depth=current_depth,
                max_depth=max_depth,
                target_url=crawl_target_url,  # 현재 크롤링 URL을 base로 사용
                scope=target.scope,
            )
            child_tasks_spawned = len(child_tasks)

        return TaskResult.create_success(
            {
                "found_links": len(links),
                "saved_assets": saved_count,
                "discovered_assets": discovery_saved_count,
                "child_tasks_spawned": child_tasks_spawned,
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
