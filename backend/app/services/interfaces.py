"""Service interface definitions using Protocol for structural subtyping.

이 모듈은 서비스 계층의 인터페이스를 Protocol로 정의합니다.
Protocol은 명시적 상속 없이 structural subtyping을 지원하므로,
기존 클래스나 Mock 객체가 메서드 시그니처만 일치하면 호환됩니다.
"""

from typing import Dict, List, Protocol, Tuple

from app.types.http import HttpData, JsContent


class ICrawler(Protocol):
    """
    웹 크롤러 인터페이스.

    CrawlerService 및 Mock 객체가 이 Protocol을 구조적으로 만족해야 합니다.
    의존성 주입 시 이 Protocol을 타입 힌트로 사용하여
    구체적인 구현에 대한 의존성을 줄입니다.

    Example:
        ```python
        class CrawlWorker:
            def __init__(self, crawler: ICrawler):
                self.crawler = crawler

        # 실제 구현체
        worker = CrawlWorker(CrawlerService())

        # Mock 주입 (테스트)
        mock_crawler = MagicMock()
        mock_crawler.crawl = AsyncMock(return_value=([], {}, []))
        worker = CrawlWorker(mock_crawler)
        ```
    """

    async def crawl(
        self, url: str
    ) -> Tuple[List[str], Dict[str, HttpData], List[JsContent]]:
        """
        페이지를 크롤링하고 HTTP 데이터를 캡처합니다.

        Args:
            url: 크롤링할 대상 URL

        Returns:
            Tuple of:
            - List[str]: 발견된 고유 URL 목록
            - Dict[str, HttpData]: URL을 키로 하는 HTTP 데이터 딕셔너리
                - HttpData는 request, response, parameters 키를 가질 수 있음
            - List[JsContent]: JavaScript 파일 content 목록
        """
        ...
