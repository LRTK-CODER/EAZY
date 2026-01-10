"""
Phase 3 Day 2: CrawlWorker 테스트
TDD RED 단계 - 이 테스트들은 crawl_worker.py 구현 전에 실패해야 함
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.task import Task, TaskStatus, TaskType
from app.models.project import Project
from app.models.target import Target
from app.workers.base import WorkerContext, TaskResult


class TestCrawlWorkerTaskType:
    """CrawlWorker task_type 속성 테스트"""

    def test_crawl_worker_has_task_type_crawl(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """CrawlWorker.task_type should be TaskType.CRAWL"""
        from app.workers.crawl_worker import CrawlWorker

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = CrawlWorker(context)

        assert worker.task_type == TaskType.CRAWL


class TestCrawlWorkerDependencyInjection:
    """CrawlWorker 의존성 주입 테스트"""

    def test_crawl_worker_accepts_crawler_service(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery, mock_crawler_service
    ):
        """CrawlWorker should accept injected CrawlerService"""
        from app.workers.crawl_worker import CrawlWorker

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)

        assert worker.crawler == mock_crawler_service

    def test_crawl_worker_accepts_asset_service_factory(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """CrawlWorker should accept asset_service_factory for testing"""
        from app.workers.crawl_worker import CrawlWorker
        from app.services.asset_service import AssetService

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        custom_factory = lambda s: AssetService(s)
        worker = CrawlWorker(context, asset_service_factory=custom_factory)

        assert worker.asset_service_factory == custom_factory

    def test_crawl_worker_creates_default_services_if_not_provided(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """CrawlWorker should create default services when not injected"""
        from app.workers.crawl_worker import CrawlWorker
        from app.services.crawler_service import CrawlerService

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = CrawlWorker(context)

        assert isinstance(worker.crawler, CrawlerService)
        assert worker.asset_service_factory is not None


class TestCrawlWorkerExecute:
    """CrawlWorker execute() 메서드 테스트"""

    @pytest.fixture
    async def setup_test_data(self, db_session):
        """Create test project, target, and task"""
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(name="Test Target", project_id=project.id, url="http://example.com")
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.mark.asyncio
    async def test_execute_fetches_target(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should fetch Target from database"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock to capture the URL passed to crawl
        captured_url = None
        async def capture_crawl(url):
            nonlocal captured_url
            captured_url = url
            return ([], {})

        mock_crawler_service.crawl = capture_crawl

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        assert captured_url == "http://example.com"

    @pytest.mark.asyncio
    async def test_execute_calls_crawler_crawl(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should call crawler.crawl() with target URL"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(["http://example.com/page1"], {}))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        mock_crawler_service.crawl.assert_called_once_with("http://example.com")

    @pytest.mark.asyncio
    async def test_execute_saves_assets(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should save discovered assets"""
        from app.workers.crawl_worker import CrawlWorker
        from app.models.asset import Asset
        from sqlmodel import select

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(
            ["http://example.com/page1", "http://example.com/page2"],
            {
                "http://example.com/page1": {
                    "request": {"method": "GET"},
                    "response": {"status": 200},
                    "parameters": {}
                },
                "http://example.com/page2": {
                    "request": {"method": "POST"},
                    "response": {"status": 201},
                    "parameters": {}
                }
            }
        ))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        # Check assets were saved
        result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
        assets = result.all()

        assert len(assets) == 2

    @pytest.mark.asyncio
    async def test_execute_returns_success_result(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should return TaskResult with found_links count"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(
            ["http://example.com/page1", "http://example.com/page2", "http://example.com/page3"],
            {}
        ))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        assert result.success is True
        assert result.data["found_links"] == 3

    @pytest.mark.asyncio
    async def test_execute_handles_missing_target(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should raise ValueError for missing target"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": 99999}  # Non-existent target

        with pytest.raises(ValueError, match="Target 99999 not found"):
            await worker.execute(task_data, task)


class TestCrawlWorkerCancellation:
    """CrawlWorker 취소 기능 테스트"""

    @pytest.fixture
    async def setup_test_data(self, db_session):
        """Create test project, target, and task"""
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(name="Test Target", project_id=project.id, url="http://example.com")
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.RUNNING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.mark.asyncio
    async def test_execute_checks_cancellation(
        self, db_session, redis_client, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should check for cancellation during processing"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        # Set cancel flag in Redis
        await redis_client.set(f"task:{task.id}:cancel", "1")

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Return many links to trigger cancellation check
        many_links = [f"http://example.com/page{i}" for i in range(100)]
        mock_crawler_service.crawl = AsyncMock(return_value=(many_links, {}))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Should detect cancellation
        assert result.cancelled is True

        # Cleanup
        await redis_client.delete(f"task:{task.id}:cancel")

    @pytest.mark.asyncio
    async def test_execute_returns_cancelled_result_on_cancel(
        self, db_session, redis_client, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should return cancelled result when cancel flag set"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        # Set cancel flag before execution
        await redis_client.set(f"task:{task.id}:cancel", "1")

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        many_links = [f"http://example.com/page{i}" for i in range(100)]
        mock_crawler_service.crawl = AsyncMock(return_value=(many_links, {}))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        assert result.cancelled is True
        assert "cancelled" in result.data or result.data.get("message", "").lower().find("cancel") >= 0

        # Cleanup
        await redis_client.delete(f"task:{task.id}:cancel")

    @pytest.mark.asyncio
    async def test_execute_clears_cancel_flag(
        self, db_session, redis_client, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should delete Redis cancel flag after handling"""
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_test_data

        # Set cancel flag
        await redis_client.set(f"task:{task.id}:cancel", "1")

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        many_links = [f"http://example.com/page{i}" for i in range(100)]
        mock_crawler_service.crawl = AsyncMock(return_value=(many_links, {}))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        # Cancel flag should be cleared
        flag = await redis_client.get(f"task:{task.id}:cancel")
        assert flag is None


class TestCrawlWorkerHttpData:
    """CrawlWorker HTTP 데이터 추출 테스트"""

    @pytest.fixture
    async def setup_test_data(self, db_session):
        """Create test project, target, and task"""
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(name="Test Target", project_id=project.id, url="http://example.com")
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.mark.asyncio
    async def test_execute_extracts_request_data(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should extract request spec from http_data"""
        from app.workers.crawl_worker import CrawlWorker
        from app.models.asset import Asset
        from sqlmodel import select

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(
            ["http://example.com/api"],
            {
                "http://example.com/api": {
                    "request": {"method": "POST", "headers": {"Content-Type": "application/json"}},
                    "response": {"status": 200},
                    "parameters": {}
                }
            }
        ))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        # Check asset has request data
        result = await db_session.exec(select(Asset).where(Asset.url == "http://example.com/api"))
        asset = result.first()

        assert asset is not None
        assert asset.request_spec is not None
        assert asset.request_spec.get("method") == "POST"

    @pytest.mark.asyncio
    async def test_execute_extracts_response_data(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should extract response spec from http_data"""
        from app.workers.crawl_worker import CrawlWorker
        from app.models.asset import Asset
        from sqlmodel import select

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(
            ["http://example.com/api"],
            {
                "http://example.com/api": {
                    "request": {"method": "GET"},
                    "response": {"status": 404, "body": "Not Found"},
                    "parameters": {}
                }
            }
        ))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        # Check asset has response data
        result = await db_session.exec(select(Asset).where(Asset.url == "http://example.com/api"))
        asset = result.first()

        assert asset is not None
        assert asset.response_spec is not None
        assert asset.response_spec.get("status") == 404

    @pytest.mark.asyncio
    async def test_execute_extracts_parameters(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service, setup_test_data
    ):
        """execute() should extract parameters from http_data"""
        from app.workers.crawl_worker import CrawlWorker
        from app.models.asset import Asset
        from sqlmodel import select

        project, target, task = setup_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_crawler_service.crawl = AsyncMock(return_value=(
            ["http://example.com/search?q=test"],
            {
                "http://example.com/search?q=test": {
                    "request": {"method": "GET"},
                    "response": {"status": 200},
                    "parameters": {"q": ["test"], "page": ["1"]}
                }
            }
        ))

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        await worker.execute(task_data, task)

        # Check asset has parameters
        result = await db_session.exec(
            select(Asset).where(Asset.url == "http://example.com/search?q=test")
        )
        asset = result.first()

        assert asset is not None
        assert asset.parameters is not None
        assert "q" in asset.parameters


class TestURLValidation:
    """SSRF 방지를 위한 URL 검증 테스트 (Day 5 Bug Fix)"""

    @pytest.mark.parametrize("unsafe_url", [
        "http://localhost/admin",
        "http://localhost:8080/api",
        "http://127.0.0.1/admin",
        "http://127.0.0.1:8080/api",
        "http://169.254.169.254/latest/meta-data",  # AWS metadata
        "http://[::1]/internal",  # IPv6 localhost
        "http://10.0.0.1/internal",  # Private network (10.x.x.x)
        "http://192.168.1.1/router",  # Private network (192.168.x.x)
        "http://172.16.0.1/internal",  # Private network (172.16-31.x.x)
        "file:///etc/passwd",  # File scheme
        "gopher://localhost/",  # Gopher scheme
        "ftp://internal-server/",  # FTP scheme
    ])
    def test_unsafe_urls_rejected(self, unsafe_url):
        """내부 네트워크 및 위험한 URL 차단"""
        from app.workers.crawl_worker import is_safe_url
        assert not is_safe_url(unsafe_url), f"URL should be unsafe: {unsafe_url}"

    @pytest.mark.parametrize("safe_url", [
        "https://example.com/page",
        "https://api.github.com/users",
        "http://external-service.com/data",
        "https://subdomain.example.org/path",
        "http://8.8.8.8/dns",  # Public IP
    ])
    def test_safe_urls_allowed(self, safe_url):
        """외부 URL은 허용"""
        from app.workers.crawl_worker import is_safe_url
        assert is_safe_url(safe_url), f"URL should be safe: {safe_url}"

    def test_empty_url_rejected(self):
        """빈 URL 거부"""
        from app.workers.crawl_worker import is_safe_url
        assert not is_safe_url("")
        assert not is_safe_url(None)

    def test_invalid_url_rejected(self):
        """잘못된 형식의 URL 거부"""
        from app.workers.crawl_worker import is_safe_url
        assert not is_safe_url("not-a-url")
        assert not is_safe_url("://missing-scheme")

    @pytest.mark.asyncio
    async def test_execute_rejects_unsafe_url(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery,
        mock_crawler_service
    ):
        """execute()는 안전하지 않은 URL에 대해 skipped 결과 반환"""
        from app.workers.crawl_worker import CrawlWorker
        from app.workers.base import WorkerContext

        # Create test data with unsafe URL
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Unsafe Target",
            project_id=project.id,
            url="http://localhost:8080/admin"  # Unsafe internal URL
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = CrawlWorker(context, crawler_service=mock_crawler_service)
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Should return skipped result for unsafe URL
        assert result.skipped is True
        assert result.data.get("reason") == "unsafe_url"
        # Crawler should NOT be called
        mock_crawler_service.crawl.assert_not_called()
