"""
1.5 Backend - Worker 확장: 재귀 크롤링 테스트
TDD RED 단계 - CrawlWorker의 자식 Task 생성 로직 테스트
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskStatus, TaskType
from app.workers.base import WorkerContext


class TestCrawlWorkerRecursive:
    """CrawlWorker 재귀 크롤링 테스트"""

    @pytest.fixture
    async def setup_recursive_test_data(self, db_session):
        """Create test project, target, and task with recursive crawl fields"""
        project = Project(name="Recursive Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target",
            project_id=project.id,
            url="http://example.com",
            scope=TargetScope.DOMAIN,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        # Task with depth=0, max_depth=3 (재귀 크롤링 가능)
        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
            depth=0,
            max_depth=3,
            parent_task_id=None,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.fixture
    async def setup_max_depth_test_data(self, db_session):
        """Create test data with task at max depth"""
        project = Project(name="Max Depth Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target",
            project_id=project.id,
            url="http://example.com",
            scope=TargetScope.DOMAIN,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        # Task with depth=3, max_depth=3 (깊이 도달 - 재귀 크롤링 불가)
        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
            depth=3,
            max_depth=3,
            parent_task_id=None,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.mark.asyncio
    async def test_worker_spawns_child_tasks_after_crawl(
        self,
        db_session,
        redis_client,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        mock_crawler_service,
        setup_recursive_test_data,
    ):
        """
        Given: depth=0, max_depth=3인 Task, crawler가 2개 링크 발견
        When: worker.execute() 호출
        Then: CrawlManager.spawn_child_tasks 호출됨, child_tasks_spawned 포함
        """
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_recursive_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock crawler to return 2 links
        mock_crawler_service.crawl = AsyncMock(
            return_value=(
                ["http://example.com/page1", "http://example.com/page2"],
                {
                    "http://example.com/page1": {
                        "request": {"method": "GET"},
                        "response": {"status": 200},
                        "parameters": {},
                    },
                    "http://example.com/page2": {
                        "request": {"method": "GET"},
                        "response": {"status": 200},
                        "parameters": {},
                    },
                },
                [],  # js_contents
            )
        )

        # Mock CrawlManager
        mock_crawl_manager = MagicMock()
        mock_crawl_manager.spawn_child_tasks = AsyncMock(
            return_value=[
                Task(id=100, project_id=project.id, target_id=target.id),
                Task(id=101, project_id=project.id, target_id=target.id),
            ]
        )
        mock_crawl_manager_factory = MagicMock(return_value=mock_crawl_manager)

        worker = CrawlWorker(
            context,
            crawler_service=mock_crawler_service,
            crawl_manager_factory=mock_crawl_manager_factory,
        )
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Verify CrawlManager.spawn_child_tasks was called
        mock_crawl_manager.spawn_child_tasks.assert_called_once()
        call_kwargs = mock_crawl_manager.spawn_child_tasks.call_args[1]
        assert call_kwargs["parent_task_id"] == task.id
        assert call_kwargs["target_id"] == target.id
        assert call_kwargs["project_id"] == project.id
        assert call_kwargs["current_depth"] == 0
        assert call_kwargs["max_depth"] == 3

        # Verify result includes child_tasks_spawned
        assert result.success is True
        assert result.data.get("child_tasks_spawned") == 2

    @pytest.mark.asyncio
    async def test_worker_stops_at_max_depth(
        self,
        db_session,
        redis_client,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        mock_crawler_service,
        setup_max_depth_test_data,
    ):
        """
        Given: depth=3, max_depth=3인 Task (깊이 도달)
        When: worker.execute() 호출
        Then: spawn_child_tasks 호출 안됨, child_tasks_spawned=0
        """
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_max_depth_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock crawler to return links
        mock_crawler_service.crawl = AsyncMock(
            return_value=(
                ["http://example.com/page1"],
                {
                    "http://example.com/page1": {
                        "request": {"method": "GET"},
                        "response": {"status": 200},
                        "parameters": {},
                    },
                },
                [],  # js_contents
            )
        )

        # Mock CrawlManager - should NOT be called
        mock_crawl_manager = MagicMock()
        mock_crawl_manager.spawn_child_tasks = AsyncMock(return_value=[])
        mock_crawl_manager_factory = MagicMock(return_value=mock_crawl_manager)

        worker = CrawlWorker(
            context,
            crawler_service=mock_crawler_service,
            crawl_manager_factory=mock_crawl_manager_factory,
        )
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Verify CrawlManager.spawn_child_tasks was NOT called (max depth reached)
        mock_crawl_manager.spawn_child_tasks.assert_not_called()

        # Verify result
        assert result.success is True
        assert result.data.get("child_tasks_spawned") == 0

    @pytest.mark.asyncio
    async def test_worker_does_not_spawn_when_no_links(
        self,
        db_session,
        redis_client,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        mock_crawler_service,
        setup_recursive_test_data,
    ):
        """
        Given: depth=0인 Task, 링크 발견 없음
        When: worker.execute() 호출
        Then: spawn_child_tasks 호출 안됨, child_tasks_spawned=0
        """
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_recursive_test_data

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock crawler to return no links
        mock_crawler_service.crawl = AsyncMock(return_value=([], {}, []))

        # Mock CrawlManager
        mock_crawl_manager = MagicMock()
        mock_crawl_manager.spawn_child_tasks = AsyncMock(return_value=[])
        mock_crawl_manager_factory = MagicMock(return_value=mock_crawl_manager)

        worker = CrawlWorker(
            context,
            crawler_service=mock_crawler_service,
            crawl_manager_factory=mock_crawl_manager_factory,
        )
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Verify spawn_child_tasks was NOT called (no links)
        mock_crawl_manager.spawn_child_tasks.assert_not_called()

        # Verify result
        assert result.success is True
        assert result.data.get("child_tasks_spawned") == 0
        assert result.data.get("found_links") == 0

    @pytest.fixture
    async def setup_child_task_with_crawl_url(self, db_session):
        """Create test data with child task that has crawl_url set"""
        project = Project(name="Child Task Test Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        target = Target(
            name="Test Target",
            project_id=project.id,
            url="http://example.com",  # root URL
            scope=TargetScope.DOMAIN,
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

        # Child task with crawl_url set (should crawl this URL, not target.url)
        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
            depth=1,
            max_depth=3,
            parent_task_id=None,
            crawl_url="http://example.com/login",  # 크롤링할 URL
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        return project, target, task

    @pytest.mark.asyncio
    async def test_worker_crawls_crawl_url_not_target_url(
        self,
        db_session,
        redis_client,
        mock_task_manager,
        mock_dlq_manager,
        mock_orphan_recovery,
        mock_crawler_service,
        setup_child_task_with_crawl_url,
    ):
        """
        Given: crawl_url이 설정된 child task
        When: worker.execute() 호출
        Then: crawler가 crawl_url을 크롤링 (target.url이 아닌)
        """
        from app.workers.crawl_worker import CrawlWorker

        project, target, task = setup_child_task_with_crawl_url

        context = WorkerContext(
            session=db_session,
            task_manager=mock_task_manager,
            dlq_manager=mock_dlq_manager,
            orphan_recovery=mock_orphan_recovery,
        )

        # Mock crawler
        mock_crawler_service.crawl = AsyncMock(
            return_value=(
                [],  # no links
                {},  # no http_data
                [],  # js_contents
            )
        )

        # Mock CrawlManager
        mock_crawl_manager = MagicMock()
        mock_crawl_manager.spawn_child_tasks = AsyncMock(return_value=[])
        mock_crawl_manager_factory = MagicMock(return_value=mock_crawl_manager)

        worker = CrawlWorker(
            context,
            crawler_service=mock_crawler_service,
            crawl_manager_factory=mock_crawl_manager_factory,
        )
        task_data = {"db_task_id": task.id, "target_id": target.id}

        result = await worker.execute(task_data, task)

        # Verify crawler was called with crawl_url, NOT target.url
        mock_crawler_service.crawl.assert_called_once_with("http://example.com/login")

        # Verify result
        assert result.success is True
