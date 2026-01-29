"""Pipeline Context - Stage 간 데이터 공유."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, cast

if TYPE_CHECKING:
    from app.infrastructure.ports.crawler import CrawlData


@dataclass
class OrchestratorResult:
    """파이프라인 실행 최종 결과.

    Attributes:
        success: 전체 실행 성공 여부
        saved_assets: 저장된 자산 수
        child_tasks_spawned: 생성된 하위 태스크 수
        found_links: 발견된 링크 수
        discovered_assets: 발견된 자산 수
        cancelled: 취소 여부
        errors: 발생한 에러 목록 [(stage_name, error_message), ...]
    """

    success: bool = True
    saved_assets: int = 0
    child_tasks_spawned: int = 0
    found_links: int = 0
    discovered_assets: int = 0
    cancelled: bool = False
    errors: List[Tuple[str, str]] = field(default_factory=list)


class PipelineContext:
    """파이프라인 컨텍스트 - Stage 간 데이터 공유.

    각 Stage는 이 컨텍스트를 통해 데이터를 읽고 쓰며,
    파이프라인 전체에서 공유되는 상태를 관리합니다.

    Attributes:
        task: 현재 처리 중인 Task
        target_id: Target ID
    """

    def __init__(self, task: Any, target_id: int):
        """PipelineContext 초기화.

        Args:
            task: 처리할 Task 객체
            target_id: Target ID
        """
        self._task = task
        self._target_id = target_id
        self._target: Optional[Any] = None
        self._crawl_data: Optional["CrawlData"] = None
        self._discovered_assets: List[Any] = []
        self._saved_count: int = 0
        self._child_tasks_spawned: int = 0
        self._is_cancelled: bool = False
        self._errors: List[Tuple[str, Exception]] = []

    @property
    def task(self) -> Any:
        """현재 Task."""
        return self._task

    @property
    def target_id(self) -> int:
        """Target ID."""
        return self._target_id

    @property
    def target(self) -> Optional[Any]:
        """현재 Target (load 후 사용 가능)."""
        return self._target

    @property
    def crawl_url(self) -> str:
        """크롤링할 URL.

        task.crawl_url이 있으면 그 값을, 없으면 target.url을 반환.
        """
        if self._task.crawl_url:
            return cast(str, self._task.crawl_url)
        if self._target:
            return cast(str, self._target.url)
        return ""

    @property
    def crawl_data(self) -> Optional["CrawlData"]:
        """크롤링 결과 데이터."""
        return self._crawl_data

    @property
    def discovered_assets(self) -> List[Any]:
        """발견된 자산 목록."""
        return self._discovered_assets

    @property
    def saved_count(self) -> int:
        """저장된 자산 수."""
        return self._saved_count

    @property
    def child_tasks_spawned(self) -> int:
        """생성된 하위 태스크 수."""
        return self._child_tasks_spawned

    @property
    def is_cancelled(self) -> bool:
        """취소 여부."""
        return self._is_cancelled

    @property
    def errors(self) -> List[Tuple[str, Exception]]:
        """발생한 에러 목록."""
        return self._errors

    @property
    def depth(self) -> int:
        """현재 크롤 깊이."""
        return cast(int, self._task.depth)

    @property
    def max_depth(self) -> int:
        """최대 크롤 깊이."""
        return cast(int, self._task.max_depth)

    @property
    def project_id(self) -> int:
        """프로젝트 ID."""
        return cast(int, self._task.project_id)

    def set_target(self, target: Any) -> None:
        """Target 설정.

        Args:
            target: Target 객체
        """
        self._target = target

    def set_crawl_data(self, data: "CrawlData") -> None:
        """크롤링 결과 데이터 설정.

        Args:
            data: CrawlData 객체
        """
        self._crawl_data = data

    def set_discovered_assets(self, assets: List[Any]) -> None:
        """발견된 자산 목록 설정.

        Args:
            assets: 자산 목록
        """
        self._discovered_assets = assets

    def set_saved_count(self, count: int) -> None:
        """저장된 자산 수 설정.

        Args:
            count: 저장된 자산 수
        """
        self._saved_count = count

    def set_child_tasks_spawned(self, count: int) -> None:
        """생성된 하위 태스크 수 설정.

        Args:
            count: 생성된 태스크 수
        """
        self._child_tasks_spawned = count

    def mark_cancelled(self) -> None:
        """취소 상태로 설정."""
        self._is_cancelled = True

    def add_error(self, stage_name: str, error: Exception) -> None:
        """에러 추가.

        Args:
            stage_name: 에러가 발생한 Stage 이름
            error: 발생한 예외
        """
        self._errors.append((stage_name, error))

    def to_result(self) -> OrchestratorResult:
        """컨텍스트를 OrchestratorResult로 변환.

        Returns:
            OrchestratorResult: 파이프라인 실행 결과
        """
        # 에러를 (stage_name, error_message) 형태로 변환
        error_tuples = [(stage, str(err)) for stage, err in self._errors]

        # Calculate found_links from crawl_data
        found_links = 0
        if self._crawl_data:
            found_links = len(self._crawl_data.links)

        return OrchestratorResult(
            success=len(self._errors) == 0 and not self._is_cancelled,
            saved_assets=self._saved_count,
            child_tasks_spawned=self._child_tasks_spawned,
            found_links=found_links,
            discovered_assets=len(self._discovered_assets),
            cancelled=self._is_cancelled,
            errors=error_tuples,
        )
