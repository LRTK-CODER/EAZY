"""CrawlerAdapter 테스트."""

import pytest

from app.infrastructure.adapters.crawler_adapter import CrawlerAdapter
from app.infrastructure.ports.crawler import CrawlData


class MockCrawlerService:
    """테스트용 CrawlerService Mock."""

    async def crawl(self, url: str):
        """Mock crawl 메서드."""
        return (
            ["http://example.com/page1"],
            {"http://example.com": {"status": 200}},
            [
                {
                    "url": "http://example.com/script.js",
                    "content": "console.log('test')",
                    "content_type": "application/javascript",
                    "is_inline": False,
                }
            ],
        )


@pytest.mark.asyncio
async def test_crawler_adapter_converts_tuple_to_crawl_data():
    """CrawlerAdapter가 tuple을 CrawlData로 변환하는지 테스트."""
    mock_service = MockCrawlerService()
    adapter = CrawlerAdapter(mock_service)

    result = await adapter.crawl("http://example.com")

    assert isinstance(result, CrawlData)
    assert result.links == ["http://example.com/page1"]
    assert result.http_data == {"http://example.com": {"status": 200}}
    assert len(result.js_contents) == 1
    assert result.js_contents[0]["url"] == "http://example.com/script.js"


@pytest.mark.asyncio
async def test_crawler_adapter_with_empty_results():
    """빈 크롤링 결과를 처리하는지 테스트."""

    class EmptyCrawlerService:
        async def crawl(self, url: str):
            return [], {}, []

    adapter = CrawlerAdapter(EmptyCrawlerService())
    result = await adapter.crawl("http://example.com")

    assert isinstance(result, CrawlData)
    assert result.links == []
    assert result.http_data == {}
    assert result.js_contents == []


@pytest.mark.asyncio
async def test_crawler_adapter_propagates_exceptions():
    """CrawlerService의 예외를 전파하는지 테스트."""

    class FailingCrawlerService:
        async def crawl(self, url: str):
            raise ValueError("Crawl failed")

    adapter = CrawlerAdapter(FailingCrawlerService())

    with pytest.raises(ValueError, match="Crawl failed"):
        await adapter.crawl("http://example.com")
