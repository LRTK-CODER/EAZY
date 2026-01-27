"""ICrawler Protocol 테스트.

TDD RED Phase: ICrawler Protocol이 올바르게 정의되고,
CrawlerService와 Mock 객체가 이를 만족하는지 테스트합니다.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestICrawlerProtocol:
    """ICrawler Protocol 정의 테스트."""

    def test_icrawler_protocol_has_crawl_method(self):
        """ICrawler Protocol이 crawl 메서드를 정의하는지 확인."""
        from app.services.interfaces import ICrawler

        assert "crawl" in dir(ICrawler)

    def test_icrawler_crawl_method_is_async(self):
        """crawl 메서드가 async 함수인지 확인."""
        from app.services.interfaces import ICrawler

        assert inspect.iscoroutinefunction(ICrawler.crawl)

    def test_icrawler_crawl_has_url_parameter(self):
        """crawl 메서드가 url 파라미터를 받는지 확인."""
        from app.services.interfaces import ICrawler

        sig = inspect.signature(ICrawler.crawl)
        assert "url" in sig.parameters


class TestCrawlerServiceImplementsICrawler:
    """CrawlerService가 ICrawler를 구현하는지 확인."""

    def test_crawler_service_has_crawl_method(self):
        """CrawlerService가 crawl 메서드를 가지는지 확인."""
        from app.services.crawler_service import CrawlerService

        crawler = CrawlerService()
        assert hasattr(crawler, "crawl")
        assert callable(crawler.crawl)

    def test_crawler_service_crawl_is_async(self):
        """CrawlerService.crawl이 async 함수인지 확인."""
        from app.services.crawler_service import CrawlerService

        crawler = CrawlerService()
        assert inspect.iscoroutinefunction(crawler.crawl)

    def test_crawler_service_crawl_has_url_parameter(self):
        """CrawlerService.crawl이 url 파라미터를 받는지 확인."""
        from app.services.crawler_service import CrawlerService

        crawler = CrawlerService()
        sig = inspect.signature(crawler.crawl)
        assert "url" in sig.parameters


class TestMockCrawlerImplementsICrawler:
    """Mock 크롤러가 ICrawler Protocol을 만족하는지 확인."""

    @pytest.mark.asyncio
    async def test_mock_crawler_can_be_used_as_icrawler(self):
        """Mock 객체가 ICrawler처럼 사용 가능한지 확인."""
        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(
            return_value=(
                ["http://example.com/page1"],
                {
                    "http://example.com/page1": {
                        "request": {"method": "GET", "headers": {}, "body": None},
                        "response": {"status": 200, "headers": {}, "body": "<html>"},
                    }
                },
                [],  # js_contents
            )
        )

        # crawl 호출 및 반환값 검증
        links, http_data, js_contents = await mock_crawler.crawl("http://example.com")

        assert isinstance(links, list)
        assert isinstance(http_data, dict)
        assert isinstance(js_contents, list)
        mock_crawler.crawl.assert_called_once_with("http://example.com")

    @pytest.mark.asyncio
    async def test_mock_crawler_returns_correct_structure(self):
        """Mock crawl()이 올바른 구조를 반환하는지 확인."""
        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(
            return_value=(
                ["http://example.com/page1", "http://example.com/page2"],
                {
                    "http://example.com/page1": {
                        "request": {
                            "method": "GET",
                            "headers": {"User-Agent": "Test"},
                            "body": None,
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "text/html"},
                            "body": "<html>",
                        },
                        "parameters": {"id": "123"},
                    }
                },
                [],  # js_contents
            )
        )

        links, http_data, js_contents = await mock_crawler.crawl("http://example.com")

        # 반환 구조 검증
        assert len(links) == 2
        assert "http://example.com/page1" in http_data
        assert "request" in http_data["http://example.com/page1"]
        assert "response" in http_data["http://example.com/page1"]
