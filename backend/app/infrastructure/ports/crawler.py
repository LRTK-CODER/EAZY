"""Crawler port interface."""

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from app.types.http import JsContent


@dataclass
class CrawlData:
    """크롤링 결과 데이터 (기존 tuple 반환값을 구조화)"""

    links: List[str]
    http_data: Dict[str, Any]
    js_contents: List[JsContent]


class ICrawler(Protocol):
    """크롤러 인터페이스 - CrawlerService.crawl()을 래핑"""

    async def crawl(self, url: str) -> CrawlData:
        """
        URL을 크롤링하고 결과 반환.

        Args:
            url: 크롤링할 URL

        Returns:
            CrawlData containing links, http_data, js_contents
        """
        ...
