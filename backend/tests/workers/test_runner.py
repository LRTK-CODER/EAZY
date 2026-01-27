"""
Phase 3 Day 4: Worker Runner 테스트
TDD RED 단계 - 이 테스트들은 runner.py 구현 전에 실패해야 함
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.project import Project
from app.models.target import Target
from app.models.task import Task, TaskStatus, TaskType
from app.workers.base import WorkerContext


class TestProcessOneTask:
    """process_one_task() 함수 테스트"""

    @pytest.mark.asyncio
    async def test_process_one_task_returns_false_on_empty_queue(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should return False when queue is empty"""
        from app.workers.runner import process_one_task

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock empty queue
        mock_task_manager.dequeue_task = AsyncMock(return_value=None)

        result = await process_one_task(context)

        assert result is False

    @pytest.mark.asyncio
    async def test_process_one_task_dequeues_from_task_manager(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should call task_manager.dequeue_task()"""
        from app.workers.runner import process_one_task

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        mock_task_manager.dequeue_task = AsyncMock(return_value=None)

        await process_one_task(context)

        mock_task_manager.dequeue_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_one_task_creates_correct_worker(
        self, db_session, redis_client, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should create worker for task type"""
        from app.core.queue import TaskManager
        from app.workers.runner import process_one_task

        # Create real test data
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target", project_id=project.id, url="http://example.com"
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

        task_manager = TaskManager(redis_client)

        context = WorkerContext(
            session=db_session,
            task_manager=task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        task_data = {
            "id": "test-uuid",
            "db_task_id": task.id,
            "target_id": target.id,
            "type": "crawl",
        }
        task_json = json.dumps(task_data)

        # Push task to queue
        await redis_client.rpush("eazy_task_queue", task_json)

        # Mock crawler to avoid actual crawling
        with patch("app.workers.crawl_worker.CrawlerService") as MockCrawler:
            mock_crawler = MockCrawler.return_value
            mock_crawler.crawl = AsyncMock(return_value=([], {}, []))
            mock_orphan_recovery.send_heartbeat = AsyncMock()
            mock_orphan_recovery.clear_heartbeat = AsyncMock()

            result = await process_one_task(context)

        assert result is True

        # Cleanup
        await redis_client.delete("eazy_task_queue")
        await redis_client.delete("eazy_task_queue:processing")

    @pytest.mark.asyncio
    async def test_process_one_task_returns_true_on_success(
        self, db_session, redis_client, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should return True after processing"""
        from app.core.queue import TaskManager
        from app.workers.runner import process_one_task

        # Create test data
        project = Project(name="Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target", project_id=project.id, url="http://example.com"
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

        task_manager = TaskManager(redis_client)

        context = WorkerContext(
            session=db_session,
            task_manager=task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        task_data = {
            "id": "test-uuid",
            "db_task_id": task.id,
            "target_id": target.id,
            "type": "crawl",
        }
        task_json = json.dumps(task_data)

        await redis_client.rpush("eazy_task_queue", task_json)

        with patch("app.workers.crawl_worker.CrawlerService") as MockCrawler:
            mock_crawler = MockCrawler.return_value
            mock_crawler.crawl = AsyncMock(return_value=([], {}, []))
            mock_orphan_recovery.send_heartbeat = AsyncMock()
            mock_orphan_recovery.clear_heartbeat = AsyncMock()

            result = await process_one_task(context)

        assert result is True

        # Cleanup
        await redis_client.delete("eazy_task_queue")
        await redis_client.delete("eazy_task_queue:processing")

    @pytest.mark.asyncio
    async def test_process_one_task_handles_unknown_task_type(
        self, db_session, redis_client, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should ACK unknown task types"""
        from app.core.queue import TaskManager
        from app.workers.runner import process_one_task

        task_manager = TaskManager(redis_client)

        context = WorkerContext(
            session=db_session,
            task_manager=task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        task_data = {
            "id": "test-uuid",
            "db_task_id": 9999,
            "target_id": 9999,
            "type": "unknown_type",
        }
        task_json = json.dumps(task_data)

        await redis_client.rpush("eazy_task_queue", task_json)

        result = await process_one_task(context)

        # Should return True (task was handled) but task type was unknown
        assert result is True

        # Processing queue should be empty (task was ACKed)
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

        # Cleanup
        await redis_client.delete("eazy_task_queue")

    @pytest.mark.asyncio
    async def test_process_one_task_handles_invalid_task_data(
        self, db_session, redis_client, mock_dlq_manager, mock_orphan_recovery
    ):
        """process_one_task() should ACK invalid task data"""
        from app.core.queue import TaskManager
        from app.workers.runner import process_one_task

        task_manager = TaskManager(redis_client)

        context = WorkerContext(
            session=db_session,
            task_manager=task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Push invalid task (missing required fields)
        task_data = {"id": "test-uuid"}  # Missing db_task_id, target_id
        task_json = json.dumps(task_data)

        await redis_client.rpush("eazy_task_queue", task_json)

        result = await process_one_task(context)

        assert result is True

        # Cleanup
        await redis_client.delete("eazy_task_queue")
        await redis_client.delete("eazy_task_queue:processing")


class TestCreateWorkerContext:
    """create_worker_context() 함수 테스트"""

    @pytest.mark.asyncio
    async def test_create_context_creates_all_dependencies(
        self, db_session, redis_client
    ):
        """create_worker_context() should create all required managers"""
        from app.workers.runner import create_worker_context

        context = create_worker_context(db_session, redis_client)

        assert context.session == db_session
        assert context.task_manager is not None
        assert context.dlq_manager is not None
        assert context.orphan_recovery is not None

    @pytest.mark.asyncio
    async def test_create_context_shares_redis_connection(
        self, db_session, redis_client
    ):
        """create_worker_context() should share Redis between managers"""
        from app.workers.runner import create_worker_context

        context = create_worker_context(db_session, redis_client)

        # All managers should use the same Redis connection
        assert context.task_manager.redis == redis_client
        assert context.dlq_manager.redis == redis_client
        assert context.orphan_recovery.redis == redis_client


class TestIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_crawl_task_flow(
        self, db_session, redis_client, mock_dlq_manager, mock_orphan_recovery
    ):
        """Integration: Enqueue crawl task and process via runner"""
        from app.core.queue import TaskManager
        from app.workers.runner import create_worker_context, process_one_task

        # Create test data
        project = Project(name="Integration Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Integration Target",
            project_id=project.id,
            url="http://integration.test",
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

        # Enqueue task
        task_manager = TaskManager(redis_client)
        await task_manager.enqueue_crawl_task(project.id, target.id, task.id)

        # Create context
        context = create_worker_context(db_session, redis_client)

        # Process with mocked crawler
        with patch("app.workers.crawl_worker.CrawlerService") as MockCrawler:
            mock_crawler = MockCrawler.return_value
            mock_crawler.crawl = AsyncMock(
                return_value=(
                    ["http://integration.test/page1"],
                    {
                        "http://integration.test/page1": {
                            "request": {"method": "GET"},
                            "response": {"status": 200},
                            "parameters": {},
                        }
                    },
                    [],  # js_contents
                )
            )

            result = await process_one_task(context)

        assert result is True

        # Verify task status changed
        await db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED

        # Cleanup
        await redis_client.delete("eazy_task_queue")
        await redis_client.delete("eazy_task_queue:processing")


class TestPackageExports:
    """패키지 공개 API 테스트"""

    def test_package_exports_base_worker(self):
        """Package should export BaseWorker"""
        from app.workers import BaseWorker
        from app.workers.base import BaseWorker as DirectBaseWorker

        assert BaseWorker is DirectBaseWorker

    def test_package_exports_worker_context(self):
        """Package should export WorkerContext"""
        from app.workers import WorkerContext
        from app.workers.base import WorkerContext as DirectWorkerContext

        assert WorkerContext is DirectWorkerContext

    def test_package_exports_task_result(self):
        """Package should export TaskResult"""
        from app.workers import TaskResult
        from app.workers.base import TaskResult as DirectTaskResult

        assert TaskResult is DirectTaskResult

    def test_package_exports_crawl_worker(self):
        """Package should export CrawlWorker"""
        from app.workers import CrawlWorker
        from app.workers.crawl_worker import CrawlWorker as DirectCrawlWorker

        assert CrawlWorker is DirectCrawlWorker

    def test_package_exports_run_worker(self):
        """Package should export run_worker"""
        from app.workers import run_worker
        from app.workers.runner import run_worker as DirectRunWorker

        assert run_worker is DirectRunWorker

    def test_package_exports_registry_functions(self):
        """Package should export registry functions"""
        from app.workers import (
            WORKER_REGISTRY,
            create_worker,
            get_worker_class,
            register_worker,
        )
        from app.workers.registry import WORKER_REGISTRY as DirectRegistry
        from app.workers.registry import create_worker as DirectCreateWorker
        from app.workers.registry import get_worker_class as DirectGetWorkerClass
        from app.workers.registry import register_worker as DirectRegisterWorker

        assert WORKER_REGISTRY is DirectRegistry
        assert get_worker_class is DirectGetWorkerClass
        assert register_worker is DirectRegisterWorker
        assert create_worker is DirectCreateWorker

    def test_package_all_exports(self):
        """Package __all__ should contain all expected exports"""
        from app import workers

        expected_exports = [
            "BaseWorker",
            "WorkerContext",
            "TaskResult",
            "CrawlWorker",
            "WORKER_REGISTRY",
            "get_worker_class",
            "register_worker",
            "create_worker",
            "run_worker",
            "process_one_task",
            "create_worker_context",
        ]

        for export in expected_exports:
            assert export in workers.__all__, f"{export} not in __all__"
            assert hasattr(workers, export), f"{export} not exported"


class TestDeprecation:
    """기존 worker 모듈 deprecation 테스트"""

    def test_old_worker_module_emits_deprecation_warning(self):
        """Importing app.worker should emit DeprecationWarning"""
        import sys
        import warnings

        # Remove from cache if already imported
        if "app.worker" in sys.modules:
            del sys.modules["app.worker"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import the deprecated module to trigger warning
            import app.worker  # noqa: F401

            # Check that a DeprecationWarning was issued
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message).lower()
