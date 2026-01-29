"""크롤링 데이터 ↔ Discovery 컨텍스트 변환.

DataTransformer는 크롤러가 수집한 HTTP 데이터를 Discovery 모듈이 이해할 수 있는 형식으로 변환합니다.
"""

from typing import Any, Dict, List

from app.models.asset import AssetSource, AssetType
from app.services.discovery.models import DiscoveryContext, ScanProfile


class DataTransformer:
    """크롤링 데이터 ↔ Discovery 컨텍스트 변환.

    Discovery 모듈과 크롤러 간의 데이터 변환을 담당합니다.
    AssetSource, AssetType 매핑과 HTTP 데이터 변환을 제공합니다.

    Example:
        >>> transformer = DataTransformer()
        >>> source = transformer.map_source("html_element_parser")
        >>> asset_type = transformer.map_type("form")
        >>> context = transformer.to_discovery_context(
        ...     target_url="https://example.com",
        ...     http_data=http_data,
        ...     http_client=client
        ... )
    """

    SOURCE_MAPPING = {
        "html_element_parser": AssetSource.HTML,
        "network_capturer": AssetSource.NETWORK,
        "js_analyzer_regex": AssetSource.JS,
        "js_analyzer_ast": AssetSource.JS,
        "config_discovery": AssetSource.HTML,
        "interaction_engine": AssetSource.DOM,
    }

    TYPE_MAPPING = {
        "form": AssetType.FORM,
        "api_endpoint": AssetType.XHR,
        "api_call": AssetType.XHR,
        "xhr": AssetType.XHR,
        "fetch": AssetType.XHR,
    }

    def map_source(self, source: str) -> AssetSource:
        """Discovery source를 AssetSource로 매핑.

        Args:
            source: Discovery 모듈 이름

        Returns:
            대응하는 AssetSource (알 수 없는 경우 AssetSource.HTML)

        Example:
            >>> transformer = DataTransformer()
            >>> transformer.map_source("html_element_parser")
            <AssetSource.HTML: 'html'>
        """
        return self.SOURCE_MAPPING.get(source, AssetSource.HTML)

    def map_type(self, asset_type: str) -> AssetType:
        """Discovery asset_type을 AssetType으로 매핑.

        Args:
            asset_type: Discovery에서 반환한 자산 유형

        Returns:
            대응하는 AssetType (알 수 없는 경우 AssetType.URL)

        Example:
            >>> transformer = DataTransformer()
            >>> transformer.map_type("form")
            <AssetType.FORM: 'form'>
        """
        return self.TYPE_MAPPING.get(asset_type, AssetType.URL)

    def transform_to_network_requests(
        self, http_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """http_data를 network_requests 형식으로 변환.

        Args:
            http_data: CrawlerService에서 반환한 HTTP 데이터
                형식: {url: {"request": {...}, "response": {...}}}

        Returns:
            NetworkCapturerModule이 필요로 하는 형식의 요청 목록

        Example:
            >>> transformer = DataTransformer()
            >>> http_data = {
            ...     "https://example.com/api": {
            ...         "request": {"method": "POST", "body": "data"}
            ...     }
            ... }
            >>> requests = transformer.transform_to_network_requests(http_data)
            >>> len(requests)
            1
        """
        network_requests: List[Dict[str, Any]] = []
        for url, data in http_data.items():
            request = data.get("request")
            if not request:
                continue
            network_requests.append(
                {
                    "url": url,
                    "method": request.get("method", "GET"),
                    "headers": request.get("headers", {}),
                    "body": request.get("body"),
                    "post_data": request.get("body"),  # NetworkCapturerModule 호환
                    "resource_type": request.get("resource_type", ""),
                }
            )
        return network_requests

    def transform_to_network_responses(
        self, http_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """http_data를 network_responses 형식으로 변환.

        Args:
            http_data: CrawlerService에서 반환한 HTTP 데이터
                형식: {url: {"request": {...}, "response": {...}}}

        Returns:
            NetworkCapturerModule이 필요로 하는 형식의 응답 목록

        Example:
            >>> transformer = DataTransformer()
            >>> http_data = {
            ...     "https://example.com/api": {
            ...         "response": {"status": 200, "body": "OK"}
            ...     }
            ... }
            >>> responses = transformer.transform_to_network_responses(http_data)
            >>> len(responses)
            1
        """
        network_responses: List[Dict[str, Any]] = []
        for url, data in http_data.items():
            response = data.get("response")
            if not response:
                continue
            network_responses.append(
                {
                    "url": url,
                    "status": response.get("status"),
                    "headers": response.get("headers", {}),
                    "body": response.get("body"),
                }
            )
        return network_responses

    def extract_html_content(self, http_data: Dict[str, Any], url: str) -> str:
        """http_data에서 HTML 컨텐츠 추출.

        Args:
            http_data: CrawlerService에서 반환한 HTTP 데이터
            url: HTML을 추출할 URL

        Returns:
            HTML 컨텐츠 (없으면 빈 문자열)

        Example:
            >>> transformer = DataTransformer()
            >>> http_data = {
            ...     "https://example.com": {
            ...         "response": {"body": "<html>Test</html>"}
            ...     }
            ... }
            >>> html = transformer.extract_html_content(http_data, "https://example.com")
            >>> html
            '<html>Test</html>'
        """
        data = http_data.get(url)
        if not data:
            return ""
        response = data.get("response")
        if not response:
            return ""
        body = response.get("body", "")
        return str(body) if body else ""

    def to_discovery_context(
        self,
        target_url: str,
        http_data: Dict[str, Any],
        http_client: Any,
        js_contents: List[str] | None = None,
        profile: ScanProfile = ScanProfile.STANDARD,
    ) -> DiscoveryContext:
        """CrawlData → DiscoveryContext 변환.

        Args:
            target_url: 스캔 대상 URL
            http_data: CrawlerService에서 반환한 HTTP 데이터
            http_client: HTTP 클라이언트 (httpx.AsyncClient)
            js_contents: 수집된 JavaScript 컨텐츠 목록 (선택)
            profile: 스캔 프로필 (기본: STANDARD)

        Returns:
            Discovery 모듈이 사용할 수 있는 DiscoveryContext

        Example:
            >>> transformer = DataTransformer()
            >>> context = transformer.to_discovery_context(
            ...     target_url="https://example.com",
            ...     http_data=http_data,
            ...     http_client=client
            ... )
            >>> context.target_url
            'https://example.com'
        """
        html_content = self.extract_html_content(http_data, target_url)
        network_requests = self.transform_to_network_requests(http_data)
        network_responses = self.transform_to_network_responses(http_data)

        return DiscoveryContext(
            target_url=target_url,
            profile=profile,
            http_client=http_client,
            crawl_data={
                "html_content": html_content,
                "js_contents": js_contents or [],
                "network_requests": network_requests,
                "network_responses": network_responses,
            },
        )
