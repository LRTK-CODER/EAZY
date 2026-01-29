"""PipelineStage 및 StageResult 단위 테스트."""

from abc import ABC

import pytest

try:
    from app.application.stages.base import PipelineStage, StageResult
except ImportError:
    pytest.skip("base module not yet implemented", allow_module_level=True)


class TestStageResult:
    """StageResult 테스트."""

    def test_ok_creates_success_result(self):
        """ok()는 성공 결과 생성."""
        result = StageResult.ok()
        assert result.success is True
        assert result.should_stop is False
        assert result.error is None

    def test_stop_creates_stop_result(self):
        """stop()은 중지 결과 생성."""
        result = StageResult.stop("reason")
        assert result.success is True
        assert result.should_stop is True
        assert result.reason == "reason"

    def test_stop_without_reason(self):
        """stop()은 이유 없이도 동작."""
        result = StageResult.stop()
        assert result.should_stop is True
        assert result.reason == ""

    def test_fail_creates_failure_result(self):
        """fail()은 실패 결과 생성."""
        result = StageResult.fail("error message")
        assert result.success is False
        assert result.should_stop is True
        assert result.error == "error message"

    def test_result_is_frozen_dataclass(self):
        """StageResult는 불변."""
        result = StageResult.ok()
        with pytest.raises(AttributeError):
            result.success = False


class TestPipelineStage:
    """PipelineStage 인터페이스 테스트."""

    def test_stage_is_abstract(self):
        """PipelineStage는 추상 클래스."""
        assert issubclass(PipelineStage, ABC)

    def test_stage_has_name_property(self):
        """Stage는 name 속성을 가져야 함."""

        class TestStage(PipelineStage):
            @property
            def name(self) -> str:
                return "test"

            async def process(self, context):
                return StageResult.ok()

        stage = TestStage()
        assert stage.name == "test"

    def test_stage_has_can_continue_on_error_default_false(self):
        """can_continue_on_error 기본값은 False."""

        class TestStage(PipelineStage):
            @property
            def name(self) -> str:
                return "test"

            async def process(self, context):
                return StageResult.ok()

        stage = TestStage()
        assert stage.can_continue_on_error is False

    def test_stage_can_override_can_continue_on_error(self):
        """can_continue_on_error 오버라이드 가능."""

        class ContinuableStage(PipelineStage):
            @property
            def name(self) -> str:
                return "continuable"

            @property
            def can_continue_on_error(self) -> bool:
                return True

            async def process(self, context):
                return StageResult.ok()

        stage = ContinuableStage()
        assert stage.can_continue_on_error is True

    @pytest.mark.asyncio
    async def test_stage_process_returns_result(self):
        """process()는 StageResult 반환."""

        class TestStage(PipelineStage):
            @property
            def name(self) -> str:
                return "test"

            async def process(self, context):
                return StageResult.ok()

        stage = TestStage()
        result = await stage.process(None)
        assert isinstance(result, StageResult)
        assert result.success is True

    def test_cannot_instantiate_without_implementing_abstract_methods(self):
        """추상 메서드 구현 없이는 인스턴스화 불가."""

        class IncompleteStage(PipelineStage):
            @property
            def name(self) -> str:
                return "incomplete"

            # process() not implemented

        with pytest.raises(TypeError):
            IncompleteStage()
