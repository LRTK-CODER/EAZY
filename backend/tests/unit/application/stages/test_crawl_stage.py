"""CrawlStage 단위 테스트."""

import logging
from typing import Any, Dict, List, Optional

import pytest

try:
    from app.application.stages.crawl_stage import CrawlStage
    from app.infrastructure.ports.crawler import CrawlData
except ImportError:
    pytest.skip("crawl_stage module not yet implemented", allow_module_level=True)


# ============================================================
# Mock classes
# ============================================================


class MockCrawler:
    """테스트용 ICrawler mock."""

    def __init__(
        self,
        links: Optional[List[str]] = None,
        http_data: Optional[Dict[str, Any]] = None,
        js_contents: Optional[List[str]] = None,
        raises: Optional[Exception] = None,
    ):
        self.links = links or []
        self.http_data = http_data or {}
        self.js_contents = js_contents or []
        self.raises = raises
        self.crawl_called = False
        self.crawled_url: Optional[str] = None

    async def crawl(self, url: str) -> CrawlData:
        self.crawl_called = True
        self.crawled_url = url
        if self.raises:
            raise self.raises
        return CrawlData(
            links=self.links,
            http_data=self.http_data,
            js_contents=self.js_contents,
        )


class MockPipelineContext:
    """테스트용 PipelineContext mock."""

    def __init__(
        self,
        crawl_url: str = "https://example.com",
        is_cancelled: bool = False,
    ):
        self._crawl_url = crawl_url
        self._is_cancelled = is_cancelled
        self.crawl_data: Optional[CrawlData] = None

    @property
    def crawl_url(self) -> str:
        return self._crawl_url

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def set_crawl_data(self, data: CrawlData) -> None:
        self.crawl_data = data


# ============================================================
# Tests
# ============================================================


class TestCrawlStageProperties:
    """CrawlStage 속성 테스트."""

    def test_stage_name_is_crawl(self):
        """Stage name은 'crawl'."""
        stage = CrawlStage(crawler=MockCrawler())
        assert stage.name == "crawl"

    def test_can_continue_on_error_is_false(self):
        """CrawlStage 에러 시 계속 불가."""
        stage = CrawlStage(crawler=MockCrawler())
        assert stage.can_continue_on_error is False


class TestCrawlStageProcess:
    """CrawlStage.process() 테스트."""

    @pytest.mark.asyncio
    async def test_crawls_url_and_stores_data(self):
        """URL 크롤링 후 데이터를 context에 저장."""
        mock_crawler = MockCrawler(
            links=["https://example.com/page1", "https://example.com/page2"],
            http_data={"url": "https://example.com", "status": 200},
            js_contents=["console.log('test')"],
        )
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        result = await stage.process(context)

        assert result.success is True
        assert result.should_stop is False
        assert context.crawl_data is not None
        assert len(context.crawl_data.links) == 2
        assert context.crawl_data.links[0] == "https://example.com/page1"

    @pytest.mark.asyncio
    async def test_passes_correct_url_to_crawler(self):
        """올바른 URL을 크롤러에 전달."""
        mock_crawler = MockCrawler()
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://target.example.com/path")

        await stage.process(context)

        assert mock_crawler.crawled_url == "https://target.example.com/path"

    @pytest.mark.asyncio
    async def test_returns_failure_on_crawler_exception(self):
        """크롤러 예외 시 실패 반환."""
        mock_crawler = MockCrawler(raises=Exception("Connection timeout"))
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        result = await stage.process(context)

        assert result.success is False
        assert result.should_stop is True
        assert "Connection timeout" in result.error

    @pytest.mark.asyncio
    async def test_returns_failure_on_timeout_error(self):
        """타임아웃 에러 시 실패 반환."""
        mock_crawler = MockCrawler(raises=TimeoutError("Request timed out"))
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://slow-site.com")

        result = await stage.process(context)

        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_crawl_data_not_set_on_failure(self):
        """실패 시 crawl_data가 설정되지 않음."""
        mock_crawler = MockCrawler(raises=Exception("Failed"))
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        await stage.process(context)

        assert context.crawl_data is None

    @pytest.mark.asyncio
    async def test_handles_empty_crawl_result(self):
        """빈 크롤링 결과 처리."""
        mock_crawler = MockCrawler(links=[], http_data={}, js_contents=[])
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        result = await stage.process(context)

        assert result.success is True
        assert context.crawl_data is not None
        assert len(context.crawl_data.links) == 0

    @pytest.mark.asyncio
    async def test_returns_stop_for_cancelled_context(self):
        """취소된 컨텍스트는 stop 반환."""
        mock_crawler = MockCrawler()
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(
            crawl_url="https://example.com", is_cancelled=True
        )

        result = await stage.process(context)

        assert result.should_stop is True
        # 크롤러가 호출되지 않아야 함
        assert mock_crawler.crawl_called is False


class TestCrawlStageLogging:
    """CrawlStage 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_crawl_completion(self, caplog):
        """크롤 완료 시 로깅."""
        mock_crawler = MockCrawler(links=["https://example.com/page1"])
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        with caplog.at_level(logging.INFO):
            await stage.process(context)

        assert any(
            "crawl" in record.message.lower()
            and (
                "complet" in record.message.lower()
                or "duration" in record.message.lower()
            )
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_crawl_failure(self, caplog):
        """크롤 실패 시 로깅."""
        mock_crawler = MockCrawler(raises=Exception("Network error"))
        stage = CrawlStage(crawler=mock_crawler)
        context = MockPipelineContext(crawl_url="https://example.com")

        with caplog.at_level(logging.ERROR):
            await stage.process(context)

        assert any(
            "fail" in record.message.lower() or "error" in record.message.lower()
            for record in caplog.records
        )
