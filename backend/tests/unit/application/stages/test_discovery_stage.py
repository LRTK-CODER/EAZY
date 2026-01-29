"""DiscoveryStage 단위 테스트."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

try:
    from app.application.stages.discovery_stage import DiscoveryStage
except ImportError:
    pytest.skip("discovery_stage module not yet implemented", allow_module_level=True)


# ============================================================
# Mock classes
# ============================================================


@dataclass
class MockDiscoveredAsset:
    """테스트용 DiscoveredAsset mock."""

    url: str = "/api/test"
    asset_type: str = "endpoint"
    source: str = "network"
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockDiscoveryService:
    """테스트용 DiscoveryService mock."""

    def __init__(
        self,
        assets: Optional[List[MockDiscoveredAsset]] = None,
        raises: Optional[Exception] = None,
    ):
        self.assets = assets or []
        self.raises = raises
        self.run_called = False
        self.last_context: Any = None

    async def run(self, context: Any) -> List[MockDiscoveredAsset]:
        self.run_called = True
        self.last_context = context
        if self.raises:
            raise self.raises
        return self.assets


class MockDataTransformer:
    """테스트용 DataTransformer mock."""

    def __init__(self):
        self.to_discovery_context_called = False
        self._context = MagicMock()  # Returns a mock DiscoveryContext

    def to_discovery_context(self, **kwargs: Any) -> Any:
        self.to_discovery_context_called = True
        return self._context


@dataclass
class MockCrawlData:
    """테스트용 CrawlData mock."""

    links: List[str] = field(default_factory=list)
    http_data: Dict[str, Any] = field(default_factory=dict)
    js_contents: List[str] = field(default_factory=list)


class MockPipelineContext:
    """테스트용 PipelineContext mock."""

    def __init__(
        self,
        crawl_url: str = "https://example.com",
        crawl_data: Optional[MockCrawlData] = None,
        target: Any = None,
        is_cancelled: bool = False,
    ):
        self._crawl_url = crawl_url
        self.crawl_data = crawl_data or MockCrawlData()
        self.target = target or MagicMock()
        self._is_cancelled = is_cancelled
        self.discovered_assets: List[Any] = []
        self.errors: List[tuple] = []

    @property
    def crawl_url(self) -> str:
        return self._crawl_url

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def set_discovered_assets(self, assets: List[Any]) -> None:
        self.discovered_assets = assets

    def add_error(self, stage_name: str, error: Exception) -> None:
        self.errors.append((stage_name, error))


# ============================================================
# Tests
# ============================================================


class TestDiscoveryStageProperties:
    """DiscoveryStage 속성 테스트."""

    def test_stage_name_is_discovery(self):
        """Stage name은 'discovery'."""
        stage = DiscoveryStage(
            discovery_service=MockDiscoveryService(),
            data_transformer=MockDataTransformer(),
        )
        assert stage.name == "discovery"

    def test_can_continue_on_error_is_true(self):
        """DiscoveryStage 에러 시 계속 가능."""
        stage = DiscoveryStage(
            discovery_service=MockDiscoveryService(),
            data_transformer=MockDataTransformer(),
        )
        assert stage.can_continue_on_error is True


class TestDiscoveryStageProcess:
    """DiscoveryStage.process() 테스트."""

    @pytest.mark.asyncio
    async def test_runs_discovery_and_stores_results(self):
        """Discovery 서비스 실행 후 결과를 context에 저장."""
        assets = [
            MockDiscoveredAsset(url="/api/users", asset_type="endpoint"),
            MockDiscoveredAsset(url="/form/login", asset_type="form"),
        ]
        discovery = MockDiscoveryService(assets=assets)
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(
            crawl_url="https://example.com",
            crawl_data=MockCrawlData(http_data={"test": {}}),
        )
        result = await stage.process(context)

        assert result.success is True
        assert result.should_stop is False
        assert len(context.discovered_assets) == 2

    @pytest.mark.asyncio
    async def test_calls_data_transformer(self):
        """DataTransformer를 호출하여 DiscoveryContext 생성."""
        discovery = MockDiscoveryService(assets=[])
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(
            crawl_url="https://example.com",
            crawl_data=MockCrawlData(
                http_data={"url": {}},
                js_contents=["console.log('test')"],
            ),
        )
        await stage.process(context)

        assert transformer.to_discovery_context_called is True

    @pytest.mark.asyncio
    async def test_continues_on_discovery_error(self):
        """Discovery 에러 시에도 success 반환 (can_continue_on_error=True)."""
        discovery = MockDiscoveryService(raises=RuntimeError("Module error"))
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(crawl_data=MockCrawlData())
        result = await stage.process(context)

        # 에러가 발생해도 ok 반환 (can_continue_on_error)
        assert result.success is True
        assert len(context.errors) == 1
        assert context.errors[0][0] == "discovery"

    @pytest.mark.asyncio
    async def test_returns_stop_for_cancelled_context(self):
        """취소된 컨텍스트는 stop 반환."""
        discovery = MockDiscoveryService()
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(is_cancelled=True)
        result = await stage.process(context)

        assert result.should_stop is True
        assert discovery.run_called is False

    @pytest.mark.asyncio
    async def test_returns_ok_when_no_crawl_data(self):
        """crawl_data가 없으면 ok 반환 (빈 결과)."""
        discovery = MockDiscoveryService(assets=[])
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(crawl_data=None)
        result = await stage.process(context)

        assert result.success is True
        # discovery가 호출되지 않거나 빈 결과
        assert len(context.discovered_assets) == 0

    @pytest.mark.asyncio
    async def test_passes_correct_data_to_discovery_service(self):
        """Discovery 서비스에 올바른 데이터 전달."""
        discovery = MockDiscoveryService(assets=[])
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(
            crawl_url="https://example.com",
            crawl_data=MockCrawlData(
                http_data={"https://example.com": {"response": {"status": 200}}},
            ),
        )
        await stage.process(context)

        assert discovery.run_called is True


class TestDiscoveryStageLogging:
    """DiscoveryStage 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_discovery_completion(self, caplog):
        """Discovery 완료 시 로깅."""
        assets = [MockDiscoveredAsset(url="/api/test")]
        discovery = MockDiscoveryService(assets=assets)
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(crawl_data=MockCrawlData())

        with caplog.at_level(logging.INFO):
            await stage.process(context)

        assert any("discover" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_logs_discovery_error(self, caplog):
        """Discovery 에러 시 로깅."""
        discovery = MockDiscoveryService(raises=RuntimeError("Failed"))
        transformer = MockDataTransformer()
        stage = DiscoveryStage(
            discovery_service=discovery,
            data_transformer=transformer,
        )

        context = MockPipelineContext(crawl_data=MockCrawlData())

        with caplog.at_level(logging.WARNING):
            await stage.process(context)

        assert any(
            "error" in record.message.lower() or "fail" in record.message.lower()
            for record in caplog.records
        )
