"""PipelineContext 단위 테스트."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

try:
    from app.application.context.pipeline_context import (
        OrchestratorResult,
        PipelineContext,
    )
except ImportError:
    pytest.skip("pipeline_context module not yet implemented", allow_module_level=True)


# Test fixtures
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
    project_id: int = 1
    url: str = "https://example.com"


@dataclass
class MockCrawlData:
    """테스트용 CrawlData mock."""

    links: List[str] = None
    http_data: Dict[str, Any] = None
    js_contents: List[str] = None

    def __post_init__(self):
        self.links = self.links or []
        self.http_data = self.http_data or {}
        self.js_contents = self.js_contents or []


class TestPipelineContext:
    """PipelineContext 테스트."""

    def test_context_initializes_with_task_and_target_id(self):
        """Context는 task와 target_id로 초기화."""
        task = MockTask(id=1)
        context = PipelineContext(task=task, target_id=10)
        assert context.task == task
        assert context.target_id == 10

    def test_crawl_url_returns_task_url_when_set(self):
        """crawl_url은 task.crawl_url이 설정되면 그 값 반환."""
        task = MockTask(crawl_url="https://child.example.com/page")
        target = MockTarget(url="https://example.com")
        context = PipelineContext(task=task, target_id=10)
        context._target = target
        assert context.crawl_url == "https://child.example.com/page"

    def test_crawl_url_returns_target_url_when_task_url_not_set(self):
        """crawl_url은 task.crawl_url이 없으면 target.url 반환."""
        task = MockTask(crawl_url=None)
        target = MockTarget(url="https://example.com")
        context = PipelineContext(task=task, target_id=10)
        context._target = target
        assert context.crawl_url == "https://example.com"

    def test_set_target(self):
        """set_target()은 target을 설정."""
        task = MockTask()
        context = PipelineContext(task=task, target_id=10)
        target = MockTarget()
        context.set_target(target)
        assert context.target == target

    def test_set_crawl_data(self):
        """set_crawl_data()는 크롤 데이터 저장."""
        context = PipelineContext(task=MockTask(), target_id=10)
        crawl_data = MockCrawlData(links=["https://example.com/page1"])
        context.set_crawl_data(crawl_data)
        assert context.crawl_data == crawl_data
        assert context.crawl_data.links == ["https://example.com/page1"]

    def test_set_discovered_assets(self):
        """set_discovered_assets()는 발견된 자산 저장."""
        context = PipelineContext(task=MockTask(), target_id=10)
        assets = [{"url": "https://example.com/api", "type": "endpoint"}]
        context.set_discovered_assets(assets)
        assert context.discovered_assets == assets

    def test_set_saved_count(self):
        """set_saved_count()는 저장된 자산 수 기록."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.set_saved_count(5)
        assert context.saved_count == 5

    def test_set_child_tasks_spawned(self):
        """set_child_tasks_spawned()는 생성된 하위 태스크 수 기록."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.set_child_tasks_spawned(3)
        assert context.child_tasks_spawned == 3

    def test_is_cancelled_initially_false(self):
        """is_cancelled 초기값은 False."""
        context = PipelineContext(task=MockTask(), target_id=10)
        assert context.is_cancelled is False

    def test_mark_cancelled(self):
        """mark_cancelled()는 취소 상태 설정."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.mark_cancelled()
        assert context.is_cancelled is True

    def test_add_error(self):
        """add_error()는 에러 기록."""
        context = PipelineContext(task=MockTask(), target_id=10)
        error = ValueError("test error")
        context.add_error("test_stage", error)
        assert len(context.errors) == 1
        assert context.errors[0] == ("test_stage", error)

    def test_multiple_errors(self):
        """여러 에러 기록 가능."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.add_error("stage1", ValueError("error1"))
        context.add_error("stage2", RuntimeError("error2"))
        assert len(context.errors) == 2

    def test_depth_property(self):
        """depth 속성은 task.depth 반환."""
        task = MockTask(depth=2)
        context = PipelineContext(task=task, target_id=10)
        assert context.depth == 2

    def test_max_depth_property(self):
        """max_depth 속성은 task.max_depth 반환."""
        task = MockTask(max_depth=5)
        context = PipelineContext(task=task, target_id=10)
        assert context.max_depth == 5

    def test_project_id_property(self):
        """project_id 속성은 task.project_id 반환."""
        task = MockTask(project_id=42)
        context = PipelineContext(task=task, target_id=10)
        assert context.project_id == 42


class TestOrchestratorResult:
    """OrchestratorResult 테스트."""

    def test_result_defaults(self):
        """기본값 확인."""
        result = OrchestratorResult()
        assert result.success is True
        assert result.saved_assets == 0
        assert result.child_tasks_spawned == 0
        assert result.errors == []

    def test_result_with_values(self):
        """값 설정 확인."""
        result = OrchestratorResult(
            success=False,
            saved_assets=10,
            child_tasks_spawned=5,
            errors=[("stage", "error")],
        )
        assert result.success is False
        assert result.saved_assets == 10
        assert result.child_tasks_spawned == 5
        assert len(result.errors) == 1


class TestPipelineContextToResult:
    """PipelineContext.to_result() 테스트."""

    def test_to_result_returns_orchestrator_result(self):
        """to_result()는 OrchestratorResult 반환."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.set_saved_count(5)
        context.set_child_tasks_spawned(3)
        result = context.to_result()

        assert isinstance(result, OrchestratorResult)
        assert result.saved_assets == 5
        assert result.child_tasks_spawned == 3
        assert result.success is True

    def test_to_result_includes_errors(self):
        """to_result()는 에러 포함."""
        context = PipelineContext(task=MockTask(), target_id=10)
        context.add_error("stage1", ValueError("test"))
        result = context.to_result()

        assert len(result.errors) == 1
        assert result.success is False  # 에러가 있으면 실패

    def test_to_result_success_when_no_errors(self):
        """에러가 없으면 success=True."""
        context = PipelineContext(task=MockTask(), target_id=10)
        result = context.to_result()
        assert result.success is True
