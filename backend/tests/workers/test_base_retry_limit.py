"""
Phase 1: NACK 재시도 횟수 제한 테스트

TDD Red-Green-Refactor 사이클:
1. RED: 이 테스트들이 먼저 실패해야 함
2. GREEN: base.py 수정 후 통과해야 함
3. REFACTOR: 리팩토링 후에도 통과 유지

테스트 대상:
- base.py의 skipped 결과 처리에서 retry_count 체크
- MAX_RETRIES 초과 시 DLQ로 이동 (retry=False)
"""

from unittest.mock import AsyncMock

import pytest

from app.core.retry import MAX_RETRIES


class TestSkippedTaskRetryLimit:
    """skipped 작업의 재시도 횟수 제한 테스트"""

    @pytest.mark.asyncio
    async def test_skipped_task_retries_when_under_max_retries(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """retry_count < MAX_RETRIES일 때 재시도해야 함 (retry=True)"""
        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Create test data
        project = Project(name="Test Project Retry")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        # retry_count = 0 (< MAX_RETRIES=3)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-retry-0",
            "retry_count": 0,
        }
        task_json = '{"id": "test-uuid-retry-0", "retry_count": 0}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # retry_count < MAX_RETRIES이므로 retry=True로 NACK 호출해야 함
        mock_task_manager.nack_task.assert_called_once_with(task_json, retry=True)

    @pytest.mark.asyncio
    async def test_skipped_task_retries_at_boundary(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """retry_count == MAX_RETRIES - 1일 때도 재시도해야 함 (마지막 재시도)"""
        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project Boundary")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        # retry_count = MAX_RETRIES - 1 = 2 (마지막 재시도 가능)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-boundary",
            "retry_count": MAX_RETRIES - 1,
        }
        task_json = f'{{"id": "test-uuid-boundary", "retry_count": {MAX_RETRIES - 1}}}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # retry_count == MAX_RETRIES - 1이므로 아직 retry=True
        mock_task_manager.nack_task.assert_called_once_with(task_json, retry=True)

    @pytest.mark.asyncio
    async def test_skipped_task_moves_to_dlq_when_max_retries_reached(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """retry_count >= MAX_RETRIES일 때 DLQ로 이동해야 함 (retry=False)"""
        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project DLQ")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        # retry_count = MAX_RETRIES = 3 (DLQ로 이동해야 함)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-dlq",
            "retry_count": MAX_RETRIES,
        }
        task_json = f'{{"id": "test-uuid-dlq", "retry_count": {MAX_RETRIES}}}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # retry_count >= MAX_RETRIES이므로 retry=False로 DLQ 이동
        mock_task_manager.nack_task.assert_called_once_with(task_json, retry=False)

    @pytest.mark.asyncio
    async def test_skipped_task_moves_to_dlq_when_exceeds_max_retries(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """retry_count > MAX_RETRIES일 때도 DLQ로 이동해야 함"""
        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project Exceeds")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        # retry_count = 5 (> MAX_RETRIES=3)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-exceeds",
            "retry_count": MAX_RETRIES + 2,
        }
        task_json = f'{{"id": "test-uuid-exceeds", "retry_count": {MAX_RETRIES + 2}}}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # retry_count > MAX_RETRIES이므로 retry=False로 DLQ 이동
        mock_task_manager.nack_task.assert_called_once_with(task_json, retry=False)

    @pytest.mark.asyncio
    async def test_skipped_task_handles_missing_retry_count(
        self, db_session, mock_task_manager, mock_dlq_manager, mock_orphan_recovery
    ):
        """retry_count가 없을 때 기본값 0으로 처리하고 재시도해야 함"""
        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project Missing")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        # retry_count가 없음 (기본값 0으로 처리)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-missing",
            # retry_count 없음
        }
        task_json = '{"id": "test-uuid-missing"}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        await worker.process(task_data, task_json)

        # retry_count 없으면 기본값 0이므로 retry=True
        mock_task_manager.nack_task.assert_called_once_with(task_json, retry=True)


class TestSkippedTaskLogging:
    """skipped 작업의 로깅 검증 테스트"""

    @pytest.mark.asyncio
    async def test_warning_logged_when_max_retries_exceeded(
        self,
        db_session,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        caplog,
    ):
        """MAX_RETRIES 초과 시 경고 로그 출력해야 함"""
        import logging

        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project Log Warning")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-log-warning",
            "retry_count": MAX_RETRIES,
        }
        task_json = f'{{"id": "test-uuid-log-warning", "retry_count": {MAX_RETRIES}}}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        with caplog.at_level(logging.WARNING):
            await worker.process(task_data, task_json)

        # warning 로그에 "exceeded max retries" 또는 "DLQ" 관련 메시지가 있어야 함
        assert any(
            "exceeded" in record.message.lower() or "dlq" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ), f"Expected warning log about max retries, got: {[r.message for r in caplog.records]}"

    @pytest.mark.asyncio
    async def test_info_logged_when_retrying(
        self,
        db_session,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        caplog,
    ):
        """재시도 시 info 로그 출력해야 함"""
        import logging

        from app.models.project import Project
        from app.models.target import Target
        from app.models.task import Task, TaskStatus, TaskType
        from app.workers.base import BaseWorker, TaskResult, WorkerContext

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        project = Project(name="Test Project Log Info")
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

        class SkippedWorker(BaseWorker):
            @property
            def task_type(self):
                return TaskType.CRAWL

            async def execute(self, task_data, task_record):
                return TaskResult.create_skipped({"reason": "lock_unavailable"})

        worker = SkippedWorker(context)
        task_data = {
            "db_task_id": task.id,
            "target_id": target.id,
            "id": "test-uuid-log-info",
            "retry_count": 0,
        }
        task_json = '{"id": "test-uuid-log-info", "retry_count": 0}'

        mock_task_manager.ack_task = AsyncMock(return_value=True)
        mock_task_manager.nack_task = AsyncMock(return_value=True)
        mock_orphan_recovery.send_heartbeat = AsyncMock()
        mock_orphan_recovery.clear_heartbeat = AsyncMock()

        with caplog.at_level(logging.INFO):
            await worker.process(task_data, task_json)

        # info 로그에 "skipped" 또는 "retry" 관련 메시지가 있어야 함
        assert any(
            "skipped" in record.message.lower() or "retry" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.INFO
        ), f"Expected info log about retry, got: {[r.message for r in caplog.records]}"
