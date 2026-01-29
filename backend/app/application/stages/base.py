"""Pipeline Stage 기본 인터페이스 및 결과 타입."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.application.context.pipeline_context import PipelineContext


@dataclass(frozen=True)
class StageResult:
    """Stage 실행 결과.

    Attributes:
        success: 실행 성공 여부
        should_stop: 파이프라인 중단 여부
        error: 실패 시 에러 메시지
        reason: 중단 시 사유
    """

    success: bool
    should_stop: bool = False
    error: Optional[str] = None
    reason: str = ""

    @classmethod
    def ok(cls) -> "StageResult":
        """성공 결과 생성."""
        return cls(success=True, should_stop=False)

    @classmethod
    def stop(cls, reason: str = "") -> "StageResult":
        """파이프라인 중단 결과 생성 (정상 종료).

        Args:
            reason: 중단 사유
        """
        return cls(success=True, should_stop=True, reason=reason)

    @classmethod
    def fail(cls, error: str) -> "StageResult":
        """실패 결과 생성.

        Args:
            error: 에러 메시지
        """
        return cls(success=False, should_stop=True, error=error)


class PipelineStage(ABC):
    """파이프라인 Stage 추상 베이스 클래스.

    모든 Stage는 이 클래스를 상속하고
    name 속성과 process() 메서드를 구현해야 합니다.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage 이름."""
        pass

    @property
    def can_continue_on_error(self) -> bool:
        """에러 발생 시 파이프라인 계속 진행 여부.

        기본값은 False (에러 시 중단).
        필요한 경우 서브클래스에서 오버라이드.
        """
        return False

    @abstractmethod
    async def process(self, context: "PipelineContext") -> StageResult:
        """Stage 실행.

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            StageResult: 실행 결과
        """
        pass
