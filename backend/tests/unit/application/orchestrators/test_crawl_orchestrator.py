"""CrawlOrchestrator 단위 테스트."""

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

import pytest

try:
    from app.application.context.pipeline_context import OrchestratorResult
    from app.application.orchestrators.crawl_orchestrator import CrawlOrchestrator
    from app.application.stages.base import StageResult
except ImportError:
    pytest.skip(
        "crawl_orchestrator module not yet implemented", allow_module_level=True
    )


# ============================================================
# Mock classes
# ============================================================


class MockStage:
    """테스트용 PipelineStage mock."""

    def __init__(
        self,
        name: str,
        result: Optional[StageResult] = None,
        can_continue: bool = False,
        raises: Optional[Exception] = None,
    ):
        self._name = name
        self._result = result
        self._can_continue = can_continue
        self._raises = raises
        self.process_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def can_continue_on_error(self) -> bool:
        return self._can_continue

    async def process(self, context: Any) -> StageResult:
        self.process_called = True
        if self._raises:
            raise self._raises
        return self._result or StageResult.ok()


class MockCancellation:
    """테스트용 ICancellation mock."""

    def __init__(self, is_cancelled: bool = False, cancel_after: int = -1):
        self._is_cancelled = is_cancelled
        self._cancel_after = cancel_after
        self._check_count = 0

    async def is_cancelled(self, task_id: int) -> bool:
        self._check_count += 1
        if self._cancel_after >= 0 and self._check_count > self._cancel_after:
            return True
        return self._is_cancelled


@dataclass
class MockTask:
    """테스트용 Task mock."""

    id: int = 1
    target_id: int = 10
    project_id: int = 1
    depth: int = 0
    max_depth: int = 3
    crawl_url: Optional[str] = None


# ============================================================
# Tests
# ============================================================


class TestCrawlOrchestratorExecution:
    """CrawlOrchestrator 실행 테스트."""

    @pytest.mark.asyncio
    async def test_executes_all_stages_in_order(self):
        """모든 Stage 순서대로 실행."""
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl"),
            MockStage(name="discovery"),
            MockStage(name="asset"),
            MockStage(name="recurse"),
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(
            task=MockTask(id=1),
            target_id=10,
        )

        assert result.success is True
        assert all(stage.process_called for stage in stages)

    @pytest.mark.asyncio
    async def test_returns_orchestrator_result(self):
        """OrchestratorResult 반환."""
        stages = [MockStage(name="guard")]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(MockTask(id=1), target_id=10)

        assert isinstance(result, OrchestratorResult)

    @pytest.mark.asyncio
    async def test_passes_same_context_to_all_stages(self):
        """모든 Stage에 동일한 context 전달."""
        contexts_seen: List[Any] = []

        class ContextCapture(MockStage):
            async def process(self, context: Any) -> StageResult:
                self.process_called = True
                contexts_seen.append(id(context))
                return StageResult.ok()

        stages = [
            ContextCapture(name="guard"),
            ContextCapture(name="crawl"),
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        await orchestrator.execute(MockTask(id=1), target_id=10)

        # 같은 context 객체가 전달되어야 함
        assert contexts_seen[0] == contexts_seen[1]


class TestCrawlOrchestratorStopBehavior:
    """CrawlOrchestrator 중단 동작 테스트."""

    @pytest.mark.asyncio
    async def test_stops_on_should_stop_result(self):
        """should_stop=True 시 파이프라인 중지."""
        stages = [
            MockStage(name="guard", result=StageResult.stop("blocked")),
            MockStage(name="crawl"),  # 실행되면 안됨
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        await orchestrator.execute(MockTask(id=1), target_id=10)

        assert stages[0].process_called is True
        assert stages[1].process_called is False

    @pytest.mark.asyncio
    async def test_stops_on_failure(self):
        """Stage 실패 시 파이프라인 중지."""
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl", result=StageResult.fail("error")),
            MockStage(name="discovery"),  # 실행되면 안됨
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(MockTask(id=1), target_id=10)

        assert result.success is False
        assert stages[2].process_called is False


class TestCrawlOrchestratorErrorHandling:
    """CrawlOrchestrator 에러 처리 테스트."""

    @pytest.mark.asyncio
    async def test_stops_on_exception_when_stage_cannot_continue(self):
        """can_continue_on_error=False인 Stage에서 예외 시 중지."""
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl", raises=RuntimeError("crash"), can_continue=False),
            MockStage(name="discovery"),  # 실행되면 안됨
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(MockTask(id=1), target_id=10)

        assert result.success is False
        assert stages[2].process_called is False

    @pytest.mark.asyncio
    async def test_continues_on_exception_when_stage_allows(self):
        """can_continue_on_error=True인 Stage에서 예외 시 계속."""
        stages = [
            MockStage(name="guard"),
            MockStage(
                name="discovery", can_continue=True, raises=RuntimeError("error")
            ),
            MockStage(name="asset"),  # 실행되어야 함
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(MockTask(id=1), target_id=10)

        assert stages[2].process_called is True
        # 에러가 기록되어야 함
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_records_error_in_result(self):
        """예외 발생 시 에러가 결과에 기록."""
        stages = [
            MockStage(
                name="crawl", raises=ValueError("test error"), can_continue=False
            ),
        ]
        orchestrator = CrawlOrchestrator(stages=stages)

        result = await orchestrator.execute(MockTask(id=1), target_id=10)

        assert len(result.errors) >= 1
        # 에러 메시지가 포함되어야 함
        assert any("test error" in str(err) for err in result.errors)


class TestCrawlOrchestratorCancellation:
    """CrawlOrchestrator 취소 동작 테스트."""

    @pytest.mark.asyncio
    async def test_checks_cancellation_between_stages(self):
        """Stage 간 취소 확인."""
        cancellation = MockCancellation(is_cancelled=True)
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl"),  # 실행되면 안됨
        ]
        orchestrator = CrawlOrchestrator(
            stages=stages,
            cancellation=cancellation,
        )

        await orchestrator.execute(MockTask(id=1), target_id=10)

        assert stages[1].process_called is False

    @pytest.mark.asyncio
    async def test_no_cancellation_check_without_cancellation_service(self):
        """ICancellation이 없으면 취소 체크 안함."""
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl"),
        ]
        orchestrator = CrawlOrchestrator(stages=stages)  # No cancellation

        await orchestrator.execute(MockTask(id=1), target_id=10)

        assert all(stage.process_called for stage in stages)

    @pytest.mark.asyncio
    async def test_cancellation_mid_pipeline(self):
        """파이프라인 중간에 취소."""
        # cancel_after=1 means the first check passes, second check is cancelled
        cancellation = MockCancellation(cancel_after=1)
        stages = [
            MockStage(name="guard"),
            MockStage(name="crawl"),
            MockStage(name="discovery"),  # 실행되면 안됨
        ]
        orchestrator = CrawlOrchestrator(
            stages=stages,
            cancellation=cancellation,
        )

        await orchestrator.execute(MockTask(id=1), target_id=10)

        assert stages[0].process_called is True
        assert stages[1].process_called is True
        assert stages[2].process_called is False


class TestCrawlOrchestratorLogging:
    """CrawlOrchestrator 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_pipeline_start(self, caplog):
        """파이프라인 시작 시 로깅."""
        stages = [MockStage(name="guard")]
        orchestrator = CrawlOrchestrator(stages=stages)

        with caplog.at_level(logging.INFO):
            await orchestrator.execute(MockTask(id=1), target_id=10)

        assert any(
            "pipeline" in record.message.lower() or "start" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_pipeline_completion(self, caplog):
        """파이프라인 완료 시 로깅."""
        stages = [MockStage(name="guard")]
        orchestrator = CrawlOrchestrator(stages=stages)

        with caplog.at_level(logging.INFO):
            await orchestrator.execute(MockTask(id=1), target_id=10)

        assert any(
            "complet" in record.message.lower() or "finish" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_stage_error(self, caplog):
        """Stage 에러 시 로깅."""
        stages = [MockStage(name="crawl", raises=RuntimeError("crash"))]
        orchestrator = CrawlOrchestrator(stages=stages)

        with caplog.at_level(logging.ERROR):
            await orchestrator.execute(MockTask(id=1), target_id=10)

        assert any("error" in record.message.lower() for record in caplog.records)
