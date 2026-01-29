"""AssetStage 단위 테스트."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

try:
    from app.application.stages.asset_stage import AssetStage
except ImportError:
    pytest.skip("asset_stage module not yet implemented", allow_module_level=True)


# ============================================================
# Mock classes
# ============================================================


class MockAssetRepository:
    """테스트용 IAssetRepository mock."""

    def __init__(
        self,
        batch_raises: Optional[Exception] = None,
        individual_returns: int = 1,
    ):
        self.batch_raises = batch_raises
        self.individual_returns = individual_returns
        self.saved_assets: List[Any] = []
        self._save_batch_calls: List[tuple] = []
        self._save_individual_calls: List[tuple] = []

    async def save_batch(
        self,
        assets: List[Any],
        task_id: int,
        crawler_links: Optional[List[str]] = None,
        http_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        self._save_batch_calls.append((assets, task_id, crawler_links, http_data))
        if self.batch_raises:
            raise self.batch_raises
        self.saved_assets.extend(assets)
        # Also count crawler_links if provided
        link_count = len(crawler_links) if crawler_links else 0
        return len(assets) + link_count

    async def save_individual(self, asset: Any, task_id: int) -> bool:
        self._save_individual_calls.append((asset, task_id))
        self.saved_assets.append(asset)
        return True

    async def find_by_hash(self, content_hash: str) -> Optional[Any]:
        return None

    @property
    def save_batch_call_count(self) -> int:
        return len(self._save_batch_calls)

    @property
    def save_individual_call_count(self) -> int:
        return len(self._save_individual_calls)


@dataclass
class MockDiscoveredAsset:
    """테스트용 DiscoveredAsset mock."""

    url: str = "/api/test"
    asset_type: str = "endpoint"
    source: str = "network"
    metadata: Dict[str, Any] = field(default_factory=dict)


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


class MockPipelineContext:
    """테스트용 PipelineContext mock."""

    def __init__(
        self,
        discovered_assets: Optional[List[Any]] = None,
        crawl_data: Optional[MockCrawlData] = None,
        task: Optional[MockTask] = None,
        is_cancelled: bool = False,
    ):
        self.discovered_assets = discovered_assets or []
        self.crawl_data = crawl_data
        self.task = task or MockTask()
        self._is_cancelled = is_cancelled
        self.saved_count: int = 0
        self.errors: List[tuple] = []

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def set_saved_count(self, count: int) -> None:
        self.saved_count = count

    def add_error(self, stage_name: str, error: Exception) -> None:
        self.errors.append((stage_name, error))


# ============================================================
# Tests
# ============================================================


class TestAssetStageProperties:
    """AssetStage 속성 테스트."""

    def test_stage_name_is_asset(self):
        """Stage name은 'asset'."""
        stage = AssetStage(asset_repository=MockAssetRepository())
        assert stage.name == "asset"

    def test_can_continue_on_error_is_false(self):
        """AssetStage 에러 시 계속 불가."""
        stage = AssetStage(asset_repository=MockAssetRepository())
        assert stage.can_continue_on_error is False


class TestAssetStageProcess:
    """AssetStage.process() 테스트."""

    @pytest.mark.asyncio
    async def test_saves_discovered_assets_batch(self):
        """발견된 자산을 배치 저장."""
        repo = MockAssetRepository()
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[
                MockDiscoveredAsset(url="/api/users"),
                MockDiscoveredAsset(url="/api/posts"),
            ],
        )
        result = await stage.process(context)

        assert result.success is True
        assert context.saved_count == 2
        assert repo.save_batch_call_count == 1

    @pytest.mark.asyncio
    async def test_returns_ok_with_empty_assets(self):
        """자산이 없으면 ok 반환."""
        repo = MockAssetRepository()
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(discovered_assets=[])
        result = await stage.process(context)

        assert result.success is True
        assert context.saved_count == 0

    @pytest.mark.asyncio
    async def test_handles_integrity_error_with_individual_save(self):
        """IntegrityError 시 개별 저장으로 fallback."""
        from sqlalchemy.exc import IntegrityError

        repo = MockAssetRepository(
            batch_raises=IntegrityError("duplicate", {}, None),
        )
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[
                MockDiscoveredAsset(url="/api/users"),
                MockDiscoveredAsset(url="/api/posts"),
            ],
        )
        result = await stage.process(context)

        assert result.success is True
        assert repo.save_individual_call_count == 2
        assert context.saved_count > 0

    @pytest.mark.asyncio
    async def test_returns_failure_on_unexpected_error(self):
        """예상치 못한 에러 시 실패 반환."""
        repo = MockAssetRepository(
            batch_raises=RuntimeError("Database connection lost"),
        )
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[MockDiscoveredAsset(url="/api/test")],
        )
        result = await stage.process(context)

        assert result.success is False
        assert "Database connection lost" in result.error

    @pytest.mark.asyncio
    async def test_passes_task_id_to_repository(self):
        """task_id를 repository에 전달."""
        repo = MockAssetRepository()
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            task=MockTask(id=42),
            discovered_assets=[MockDiscoveredAsset(url="/api/test")],
        )
        await stage.process(context)

        # Tuple structure: (assets, task_id, crawler_links, http_data)
        assert repo._save_batch_calls[0][1] == 42  # task_id

    @pytest.mark.asyncio
    async def test_returns_stop_for_cancelled_context(self):
        """취소된 컨텍스트는 stop 반환."""
        repo = MockAssetRepository()
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[MockDiscoveredAsset()],
            is_cancelled=True,
        )
        result = await stage.process(context)

        assert result.should_stop is True
        assert repo.save_batch_call_count == 0


class TestAssetStageLogging:
    """AssetStage 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_save_completion(self, caplog):
        """저장 완료 시 로깅."""
        repo = MockAssetRepository()
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[MockDiscoveredAsset(url="/api/test")],
        )

        with caplog.at_level(logging.INFO):
            await stage.process(context)

        assert any(
            "asset" in record.message.lower() or "save" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_integrity_error_fallback(self, caplog):
        """IntegrityError fallback 시 로깅."""
        from sqlalchemy.exc import IntegrityError

        repo = MockAssetRepository(
            batch_raises=IntegrityError("duplicate", {}, None),
        )
        stage = AssetStage(asset_repository=repo)

        context = MockPipelineContext(
            discovered_assets=[MockDiscoveredAsset()],
        )

        with caplog.at_level(logging.WARNING):
            await stage.process(context)

        assert any(
            "integrity" in record.message.lower()
            or "individual" in record.message.lower()
            or "fallback" in record.message.lower()
            for record in caplog.records
        )
