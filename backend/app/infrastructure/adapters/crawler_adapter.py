"""CrawlerAdapter - CrawlerService를 ICrawler 포트에 맞게 어댑팅."""

from app.infrastructure.ports.crawler import CrawlData
from app.services.interfaces import ICrawler as ICrawlerService


class CrawlerAdapter:
    """CrawlerService를 ICrawler 포트에 맞게 어댑팅.

    CrawlerService.crawl()의 tuple 반환값을 CrawlData로 변환합니다.
    """

    def __init__(self, crawler: ICrawlerService):
        """CrawlerAdapter 초기화.

        Args:
            crawler: CrawlerService 인스턴스
        """
        self._crawler = crawler

    async def crawl(self, url: str) -> CrawlData:
        """URL을 크롤링하고 CrawlData로 반환.

        Args:
            url: 크롤링할 URL

        Returns:
            CrawlData: 구조화된 크롤링 결과
        """
        # CrawlerService.crawl()은 (links, http_data, js_contents) tuple 반환
        links, http_data, js_contents = await self._crawler.crawl(url)

        return CrawlData(
            links=links,
            http_data=http_data,
            js_contents=js_contents,
        )
