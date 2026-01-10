"""
Phase 3 Day 3: Worker Registry 테스트
TDD RED 단계 - 이 테스트들은 registry.py 구현 전에 실패해야 함
"""
import pytest
from unittest.mock import AsyncMock

from app.models.task import TaskType
from app.workers.base import BaseWorker, WorkerContext, TaskResult


class TestWorkerRegistry:
    """WORKER_REGISTRY 테스트"""

    def test_registry_exists(self):
        """WORKER_REGISTRY dict should exist"""
        from app.workers.registry import WORKER_REGISTRY

        assert isinstance(WORKER_REGISTRY, dict)

    def test_registry_has_crawl_worker(self):
        """WORKER_REGISTRY should map TaskType.CRAWL to CrawlWorker"""
        from app.workers.registry import WORKER_REGISTRY
        from app.workers.crawl_worker import CrawlWorker

        assert TaskType.CRAWL in WORKER_REGISTRY
        assert WORKER_REGISTRY[TaskType.CRAWL] == CrawlWorker

    def test_registry_values_are_baseworker_subclasses(self):
        """All registry values should be BaseWorker subclasses"""
        from app.workers.registry import WORKER_REGISTRY

        for task_type, worker_class in WORKER_REGISTRY.items():
            assert issubclass(worker_class, BaseWorker), \
                f"{worker_class} is not a BaseWorker subclass"


class TestGetWorkerClass:
    """get_worker_class() 함수 테스트"""

    def test_get_worker_class_for_crawl(self):
        """get_worker_class(TaskType.CRAWL) should return CrawlWorker"""
        from app.workers.registry import get_worker_class
        from app.workers.crawl_worker import CrawlWorker

        worker_class = get_worker_class(TaskType.CRAWL)

        assert worker_class == CrawlWorker

    def test_get_worker_class_unknown_returns_none(self):
        """get_worker_class(unknown) should return None"""
        from app.workers.registry import get_worker_class

        # Use a non-existent task type value
        worker_class = get_worker_class("unknown_task_type")

        assert worker_class is None

    def test_get_worker_class_accepts_string(self):
        """get_worker_class should accept string task type"""
        from app.workers.registry import get_worker_class
        from app.workers.crawl_worker import CrawlWorker

        worker_class = get_worker_class("crawl")

        assert worker_class == CrawlWorker


class TestRegisterWorker:
    """register_worker() 데코레이터 테스트"""

    def test_register_worker_adds_to_registry(self):
        """register_worker() should add worker to registry"""
        from app.workers.registry import WORKER_REGISTRY, register_worker

        # Create a dummy task type for testing
        class DummyTaskType:
            TEST = "test_worker"

        @register_worker(DummyTaskType.TEST)
        class TestWorker(BaseWorker):
            @property
            def task_type(self):
                return DummyTaskType.TEST

            async def execute(self, task_data, task_record):
                return TaskResult.create_success({})

        assert DummyTaskType.TEST in WORKER_REGISTRY
        assert WORKER_REGISTRY[DummyTaskType.TEST] == TestWorker

        # Cleanup
        del WORKER_REGISTRY[DummyTaskType.TEST]

    def test_register_worker_decorator(self):
        """@register_worker decorator should register worker class"""
        from app.workers.registry import WORKER_REGISTRY, register_worker

        initial_count = len(WORKER_REGISTRY)

        @register_worker("decorator_test")
        class DecoratorTestWorker(BaseWorker):
            @property
            def task_type(self):
                return "decorator_test"

            async def execute(self, task_data, task_record):
                return TaskResult.create_success({})

        assert len(WORKER_REGISTRY) == initial_count + 1
        assert "decorator_test" in WORKER_REGISTRY

        # Cleanup
        del WORKER_REGISTRY["decorator_test"]

    def test_register_worker_validates_baseworker(self):
        """register_worker should reject non-BaseWorker classes"""
        from app.workers.registry import register_worker

        with pytest.raises(TypeError):
            @register_worker("invalid")
            class NotAWorker:
                pass


class TestCreateWorker:
    """create_worker() 팩토리 함수 테스트"""

    @pytest.mark.asyncio
    async def test_create_worker_returns_instance(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """create_worker() should return worker instance"""
        from app.workers.registry import create_worker
        from app.workers.crawl_worker import CrawlWorker

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = create_worker(TaskType.CRAWL, context)

        assert isinstance(worker, CrawlWorker)

    @pytest.mark.asyncio
    async def test_create_worker_injects_context(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """create_worker() should inject WorkerContext"""
        from app.workers.registry import create_worker

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        worker = create_worker(TaskType.CRAWL, context)

        assert worker.context == context
        assert worker.session == db_session

    @pytest.mark.asyncio
    async def test_create_worker_unknown_type_raises(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """create_worker() should raise for unknown task type"""
        from app.workers.registry import create_worker

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        with pytest.raises(ValueError, match="Unknown task type"):
            create_worker("nonexistent_task_type", context)
