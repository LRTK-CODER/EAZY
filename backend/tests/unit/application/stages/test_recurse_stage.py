"""RecurseStage 단위 테스트."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

try:
    from app.application.stages.recurse_stage import RecurseStage
except ImportError:
    pytest.skip("recurse_stage module not yet implemented", allow_module_level=True)


# ============================================================
# Mock classes
# ============================================================


class MockTaskQueue:
    """테스트용 ITaskQueue mock."""

    def __init__(self):
        self.enqueued_tasks: List[Dict[str, Any]] = []

    async def enqueue(self, task_data: Dict[str, Any], priority: Any = None) -> str:
        self.enqueued_tasks.append(task_data)
        return f"task-{len(self.enqueued_tasks)}"

    @property
    def enqueue_count(self) -> int:
        return len(self.enqueued_tasks)


class MockScopeChecker:
    """테스트용 ScopeChecker mock."""

    def __init__(
        self, in_scope_urls: Optional[List[str]] = None, all_in_scope: bool = True
    ):
        self._in_scope_urls = set(in_scope_urls) if in_scope_urls else None
        self._all_in_scope = all_in_scope

    def is_in_scope(self, url: Optional[str], target: Any = None) -> bool:
        if self._in_scope_urls is not None:
            return url in self._in_scope_urls
        return self._all_in_scope

    def filter_urls(self, urls: List[str], target: Any) -> List[str]:
        return [u for u in urls if self.is_in_scope(u, target)]


class MockUrlValidator:
    """테스트용 UrlValidator mock."""

    def __init__(self, is_safe: bool = True):
        self._is_safe = is_safe

    def is_safe(self, url: Optional[str]) -> bool:
        return self._is_safe


@dataclass
class MockCrawlData:
    """테스트용 CrawlData mock."""

    links: List[str] = field(default_factory=list)
    http_data: Dict[str, Any] = field(default_factory=dict)
    js_contents: List[str] = field(default_factory=list)


@dataclass
class MockTask:
    """테스트용 Task mock."""

    id: int = 1
    target_id: int = 10
    project_id: int = 1
    depth: int = 0
    max_depth: int = 3
    crawl_url: Optional[str] = None


@dataclass
class MockTarget:
    """테스트용 Target mock."""

    id: int = 10
    url: str = "https://example.com"
    scope: str = "domain"


class MockPipelineContext:
    """테스트용 PipelineContext mock."""

    def __init__(
        self,
        task: Optional[MockTask] = None,
        target: Optional[MockTarget] = None,
        crawl_url: str = "https://example.com",
        crawl_data: Optional[MockCrawlData] = None,
        is_cancelled: bool = False,
    ):
        self.task = task or MockTask()
        self.target = target or MockTarget()
        self._crawl_url = crawl_url
        self.crawl_data = crawl_data or MockCrawlData()
        self._is_cancelled = is_cancelled
        self.child_tasks_spawned: int = 0
        self.errors: List[tuple] = []

    @property
    def crawl_url(self) -> str:
        return self._crawl_url

    @property
    def depth(self) -> int:
        return self.task.depth

    @property
    def max_depth(self) -> int:
        return self.task.max_depth

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def set_child_tasks_spawned(self, count: int) -> None:
        self.child_tasks_spawned = count

    def add_error(self, stage_name: str, error: Exception) -> None:
        self.errors.append((stage_name, error))


# ============================================================
# Tests
# ============================================================


class TestRecurseStageProperties:
    """RecurseStage 속성 테스트."""

    def test_stage_name_is_recurse(self):
        """Stage name은 'recurse'."""
        stage = RecurseStage(
            task_queue=MockTaskQueue(),
            scope_checker=MockScopeChecker(),
        )
        assert stage.name == "recurse"

    def test_can_continue_on_error_is_false(self):
        """RecurseStage 에러 시 계속 불가."""
        stage = RecurseStage(
            task_queue=MockTaskQueue(),
            scope_checker=MockScopeChecker(),
        )
        assert stage.can_continue_on_error is False


class TestRecurseStageProcess:
    """RecurseStage.process() 테스트."""

    @pytest.mark.asyncio
    async def test_spawns_child_tasks_for_links(self):
        """링크에 대한 자식 Task 생성."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(
                links=[
                    "https://example.com/page1",
                    "https://example.com/page2",
                ]
            ),
        )
        result = await stage.process(context)

        assert result.success is True
        assert context.child_tasks_spawned == 2
        assert queue.enqueue_count == 2

    @pytest.mark.asyncio
    async def test_respects_max_depth(self):
        """max_depth 도달 시 자식 Task 미생성."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(depth=3, max_depth=3),
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
        )
        result = await stage.process(context)

        assert result.success is True
        assert context.child_tasks_spawned == 0
        assert queue.enqueue_count == 0

    @pytest.mark.asyncio
    async def test_filters_out_of_scope_urls(self):
        """범위 외 URL 필터링."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(
                in_scope_urls=["https://example.com/page1"],
            ),
        )

        context = MockPipelineContext(
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(
                links=[
                    "https://example.com/page1",
                    "https://evil.com/page2",  # 범위 외
                ]
            ),
        )
        result = await stage.process(context)

        assert result.success is True
        assert context.child_tasks_spawned == 1

    @pytest.mark.asyncio
    async def test_deduplicates_links(self):
        """중복 링크 제거."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(
                links=[
                    "https://example.com/page1",
                    "https://example.com/page1",  # 중복
                    "https://example.com/page2",
                ]
            ),
        )
        await stage.process(context)

        assert context.child_tasks_spawned == 2  # 중복 제거

    @pytest.mark.asyncio
    async def test_returns_ok_with_no_links(self):
        """링크가 없으면 ok 반환."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(),
        )

        context = MockPipelineContext(
            crawl_data=MockCrawlData(links=[]),
        )
        result = await stage.process(context)

        assert result.success is True
        assert context.child_tasks_spawned == 0

    @pytest.mark.asyncio
    async def test_returns_ok_with_no_crawl_data(self):
        """crawl_data가 없으면 ok 반환."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(),
        )

        context = MockPipelineContext(crawl_data=None)
        result = await stage.process(context)

        assert result.success is True
        assert context.child_tasks_spawned == 0

    @pytest.mark.asyncio
    async def test_child_task_has_incremented_depth(self):
        """자식 Task의 depth는 부모 +1."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(id=1, target_id=10, project_id=1, depth=1, max_depth=5),
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
        )
        await stage.process(context)

        assert queue.enqueue_count == 1
        enqueued = queue.enqueued_tasks[0]
        assert enqueued["depth"] == 2
        assert enqueued["target_id"] == 10
        assert enqueued["project_id"] == 1

    @pytest.mark.asyncio
    async def test_child_task_contains_crawl_url(self):
        """자식 Task에 crawl_url 포함."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
        )
        await stage.process(context)

        enqueued = queue.enqueued_tasks[0]
        assert "crawl_url" in enqueued
        assert "example.com" in enqueued["crawl_url"]

    @pytest.mark.asyncio
    async def test_returns_stop_for_cancelled_context(self):
        """취소된 컨텍스트는 stop 반환."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(),
        )

        context = MockPipelineContext(
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
            is_cancelled=True,
        )
        result = await stage.process(context)

        assert result.should_stop is True
        assert queue.enqueue_count == 0

    @pytest.mark.asyncio
    async def test_excludes_self_url(self):
        """현재 크롤링 중인 URL은 자식 Task에서 제외."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            crawl_url="https://example.com",
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(
                links=[
                    "https://example.com",  # self URL - should be excluded
                    "https://example.com/page1",
                ]
            ),
        )
        await stage.process(context)

        assert context.child_tasks_spawned == 1


class TestRecurseStageLogging:
    """RecurseStage 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_child_task_creation(self, caplog):
        """자식 Task 생성 시 로깅."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(all_in_scope=True),
        )

        context = MockPipelineContext(
            task=MockTask(depth=0, max_depth=3),
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
        )

        with caplog.at_level(logging.INFO):
            await stage.process(context)

        assert any(
            "recurse" in record.message.lower()
            or "child" in record.message.lower()
            or "spawn" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_max_depth_reached(self, caplog):
        """max_depth 도달 시 로깅."""
        queue = MockTaskQueue()
        stage = RecurseStage(
            task_queue=queue,
            scope_checker=MockScopeChecker(),
        )

        context = MockPipelineContext(
            task=MockTask(depth=3, max_depth=3),
            crawl_data=MockCrawlData(links=["https://example.com/page1"]),
        )

        with caplog.at_level(logging.DEBUG):
            await stage.process(context)

        assert any("depth" in record.message.lower() for record in caplog.records)
