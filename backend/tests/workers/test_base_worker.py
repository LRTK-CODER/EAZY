"""
Phase 3 Day 1: BaseWorker + WorkerContext 테스트
TDD RED 단계 - 이 테스트들은 base.py 구현 전에 실패해야 함
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from abc import ABC

from sqlmodel.ext.asyncio.session import AsyncSession


class TestWorkerContext:
    """WorkerContext 데이터클래스 테스트"""

    def test_worker_context_creation(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """WorkerContext should be created with all dependencies"""
        from app.workers.base import WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        assert context is not None

    def test_worker_context_has_session(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """WorkerContext must have session attribute"""
        from app.workers.base import WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        assert hasattr(context, "session")
        assert context.session == db_session

    def test_worker_context_has_task_manager(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """WorkerContext must have task_manager attribute"""
        from app.workers.base import WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        assert hasattr(context, "task_manager")
        assert context.task_manager == mock_task_manager

    def test_worker_context_has_dlq_manager(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """WorkerContext must have dlq_manager attribute"""
        from app.workers.base import WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        assert hasattr(context, "dlq_manager")
        assert context.dlq_manager == mock_dlq_manager

    def test_worker_context_has_recovery(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """WorkerContext must have orphan_recovery attribute"""
        from app.workers.base import WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        assert hasattr(context, "orphan_recovery")
        assert context.orphan_recovery == mock_orphan_recovery


class TestTaskResult:
    """TaskResult 데이터클래스 테스트"""

    def test_task_result_success_creation(self):
        """TaskResult.create_success() should create success result"""
        from app.workers.base import TaskResult

        result = TaskResult.create_success({"found_links": 10})

        assert result.success is True
        assert result.data == {"found_links": 10}
        assert result.error is None
        assert result.cancelled is False

    def test_task_result_failure_creation(self):
        """TaskResult.create_failure() should create failure result"""
        from app.workers.base import TaskResult

        result = TaskResult.create_failure("Connection timeout", {"partial": True})

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.data == {"partial": True}
        assert result.cancelled is False

    def test_task_result_cancelled_creation(self):
        """TaskResult.create_cancelled() should create cancelled result"""
        from app.workers.base import TaskResult

        result = TaskResult.create_cancelled({"processed": 5, "total": 10})

        assert result.success is True
        assert result.cancelled is True
        assert result.data == {"processed": 5, "total": 10}
        assert result.error is None

    def test_task_result_to_json(self):
        """TaskResult should serialize data to JSON"""
        from app.workers.base import TaskResult
        import json

        result = TaskResult.create_success({"count": 42})
        json_str = result.to_json()

        assert json.loads(json_str) == {"count": 42}


class TestBaseWorker:
    """BaseWorker 추상 클래스 테스트"""

    def test_base_worker_is_abstract(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """BaseWorker cannot be instantiated directly"""
        from app.workers.base import BaseWorker, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        with pytest.raises(TypeError):
            BaseWorker(context)

    def test_base_worker_requires_execute_method(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """Subclass must implement execute() method"""
        from app.workers.base import BaseWorker, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Incomplete subclass without execute()
        class IncompleteWorker(BaseWorker):
            @property
            def task_type(self):
                return "test"

        with pytest.raises(TypeError):
            IncompleteWorker(context)

    def test_base_worker_requires_task_type_property(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """Subclass must define task_type property"""
        from app.workers.base import BaseWorker, WorkerContext, TaskResult

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Incomplete subclass without task_type
        class IncompleteWorker(BaseWorker):
            async def execute(self, task_data, task_record):
                return TaskResult.create_success({})

        with pytest.raises(TypeError):
            IncompleteWorker(context)

    @pytest.mark.asyncio
    async def test_base_worker_process_updates_status_to_running(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process() should update task status to RUNNING"""
        from app.workers.base import BaseWorker, WorkerContext, TaskResult
        from app.models.task import Task, TaskStatus, TaskType
        from app.models.project import Project
        from app.models.target import Target

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Create test data
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

        # Create concrete worker
        class TestWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                # Check status was updated to RUNNING
                assert task_record.status == TaskStatus.RUNNING
                return TaskResult.create_success({"test": True})

        worker = TestWorker(context)
        task_data = {"db_task_id": task.id, "target_id": target.id, "id": "test-uuid"}
        task_json = "{}"

        # Mock ack_task
        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # Verify task was processed
        await db_session.refresh(task)
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]

    @pytest.mark.asyncio
    async def test_base_worker_process_calls_execute(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process() should call subclass execute() method"""
        from app.workers.base import BaseWorker, WorkerContext, TaskResult
        from app.models.task import Task, TaskStatus, TaskType
        from app.models.project import Project
        from app.models.target import Target

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Create test data
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

        execute_called = False

        class TestWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                nonlocal execute_called
                execute_called = True
                return TaskResult.create_success({"executed": True})

        worker = TestWorker(context)
        task_data = {"db_task_id": task.id, "target_id": target.id, "id": "test-uuid"}
        task_json = "{}"

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        assert execute_called is True

    @pytest.mark.asyncio
    async def test_base_worker_process_acks_on_success(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process() should ACK task on successful execution"""
        from app.workers.base import BaseWorker, WorkerContext, TaskResult
        from app.models.task import Task, TaskStatus, TaskType
        from app.models.project import Project
        from app.models.target import Target

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Create test data
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

        class TestWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_success({"done": True})

        worker = TestWorker(context)
        task_data = {"db_task_id": task.id, "target_id": target.id, "id": "test-uuid"}
        task_json = '{"id": "test-uuid"}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # Verify ack was called
        mock_task_manager.ack_task.assert_called_once_with(task_json)

    @pytest.mark.asyncio
    async def test_base_worker_sends_heartbeat(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """process() should send heartbeat during execution"""
        from app.workers.base import BaseWorker, WorkerContext, TaskResult
        from app.models.task import Task, TaskStatus, TaskType
        from app.models.project import Project
        from app.models.target import Target

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Create test data
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

        class TestWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_success({})

        worker = TestWorker(context)
        task_data = {"db_task_id": task.id, "target_id": target.id, "id": "test-uuid"}
        task_json = "{}"

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # Verify heartbeat was sent
        mock_orphan_recovery.send_heartbeat.assert_called_once_with("test-uuid")
        mock_orphan_recovery.clear_heartbeat.assert_called_once_with("test-uuid")
