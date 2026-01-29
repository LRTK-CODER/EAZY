"""DataTransformer unit tests."""

from typing import Any, Dict

from app.domain.services.data_transformer import DataTransformer
from app.models.asset import AssetSource, AssetType
from app.services.discovery.models import ScanProfile


class TestDataTransformer:
    """DataTransformer unit tests."""

    def test_map_discovery_source_html(self) -> None:
        """html_element_parser → AssetSource.HTML"""
        transformer = DataTransformer()
        assert transformer.map_source("html_element_parser") == AssetSource.HTML

    def test_map_discovery_source_network(self) -> None:
        """network_capturer → AssetSource.NETWORK"""
        transformer = DataTransformer()
        assert transformer.map_source("network_capturer") == AssetSource.NETWORK

    def test_map_discovery_source_js(self) -> None:
        """js_analyzer_* → AssetSource.JS"""
        transformer = DataTransformer()
        assert transformer.map_source("js_analyzer_regex") == AssetSource.JS
        assert transformer.map_source("js_analyzer_ast") == AssetSource.JS

    def test_map_discovery_source_dom(self) -> None:
        """interaction_engine → AssetSource.DOM"""
        transformer = DataTransformer()
        assert transformer.map_source("interaction_engine") == AssetSource.DOM

    def test_map_discovery_source_unknown(self) -> None:
        """알 수 없는 소스 → AssetSource.HTML (기본값)"""
        transformer = DataTransformer()
        assert transformer.map_source("unknown_module") == AssetSource.HTML

    def test_map_asset_type_form(self) -> None:
        """form → AssetType.FORM"""
        transformer = DataTransformer()
        assert transformer.map_type("form") == AssetType.FORM

    def test_map_asset_type_xhr(self) -> None:
        """api_endpoint, xhr, fetch → AssetType.XHR"""
        transformer = DataTransformer()
        assert transformer.map_type("api_endpoint") == AssetType.XHR
        assert transformer.map_type("xhr") == AssetType.XHR
        assert transformer.map_type("fetch") == AssetType.XHR
        assert transformer.map_type("api_call") == AssetType.XHR

    def test_map_asset_type_url(self) -> None:
        """알 수 없는 타입 → AssetType.URL (기본값)"""
        transformer = DataTransformer()
        assert transformer.map_type("unknown") == AssetType.URL

    def test_transform_to_network_requests(self) -> None:
        """http_data → network_requests 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com/api": {
                "request": {
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"key": "value"}',
                    "resource_type": "xhr",
                }
            }
        }
        requests = transformer.transform_to_network_requests(http_data)
        assert isinstance(requests, list)
        assert len(requests) == 1
        assert requests[0]["url"] == "https://example.com/api"
        assert requests[0]["method"] == "POST"
        assert requests[0]["headers"] == {"Content-Type": "application/json"}
        assert requests[0]["body"] == '{"key": "value"}'
        assert requests[0]["post_data"] == '{"key": "value"}'
        assert requests[0]["resource_type"] == "xhr"

    def test_transform_to_network_responses(self) -> None:
        """http_data → network_responses 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com/api": {
                "response": {
                    "status": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"result": "ok"}',
                }
            }
        }
        responses = transformer.transform_to_network_responses(http_data)
        assert isinstance(responses, list)
        assert len(responses) == 1
        assert responses[0]["url"] == "https://example.com/api"
        assert responses[0]["status"] == 200
        assert responses[0]["headers"] == {"Content-Type": "application/json"}
        assert responses[0]["body"] == '{"result": "ok"}'

    def test_transform_empty_http_data(self) -> None:
        """빈 http_data 처리"""
        transformer = DataTransformer()
        assert transformer.transform_to_network_requests({}) == []
        assert transformer.transform_to_network_responses({}) == []

    def test_transform_to_network_requests_no_request(self) -> None:
        """request 없는 http_data 처리"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com/api": {"response": {"status": 200}}
        }
        requests = transformer.transform_to_network_requests(http_data)
        assert requests == []

    def test_transform_to_network_responses_no_response(self) -> None:
        """response 없는 http_data 처리"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com/api": {"request": {"method": "GET"}}
        }
        responses = transformer.transform_to_network_responses(http_data)
        assert responses == []

    def test_extract_html_content(self) -> None:
        """http_data에서 HTML 컨텐츠 추출"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com": {
                "response": {"body": "<html><body>Hello</body></html>"}
            }
        }
        html = transformer.extract_html_content(http_data, "https://example.com")
        assert html == "<html><body>Hello</body></html>"

    def test_extract_html_content_url_not_found(self) -> None:
        """존재하지 않는 URL에 대한 HTML 추출"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com": {"response": {"body": "<html>Test</html>"}}
        }
        html = transformer.extract_html_content(http_data, "https://other.com")
        assert html == ""

    def test_extract_html_content_no_response(self) -> None:
        """response 없는 경우 HTML 추출"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com": {"request": {"method": "GET"}}
        }
        html = transformer.extract_html_content(http_data, "https://example.com")
        assert html == ""

    def test_to_discovery_context(self) -> None:
        """CrawlData → DiscoveryContext 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com": {
                "request": {"method": "GET"},
                "response": {"body": "<html>Test</html>", "status": 200},
            }
        }
        # Mock http_client for frozen dataclass
        mock_http_client = object()

        context = transformer.to_discovery_context(
            target_url="https://example.com",
            http_data=http_data,
            js_contents=["var x = 1;"],
            http_client=mock_http_client,
        )
        assert context.target_url == "https://example.com"
        assert context.crawl_data["html_content"] == "<html>Test</html>"
        assert context.crawl_data["js_contents"] == ["var x = 1;"]
        assert len(context.crawl_data["network_requests"]) == 1
        assert len(context.crawl_data["network_responses"]) == 1
        assert context.profile == ScanProfile.STANDARD

    def test_to_discovery_context_with_profile(self) -> None:
        """프로필 지정한 DiscoveryContext 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {}
        mock_http_client = object()

        context = transformer.to_discovery_context(
            target_url="https://example.com",
            http_data=http_data,
            http_client=mock_http_client,
            profile=ScanProfile.FULL,
        )
        assert context.profile == ScanProfile.FULL

    def test_to_discovery_context_without_js_contents(self) -> None:
        """js_contents 없는 DiscoveryContext 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {}
        mock_http_client = object()

        context = transformer.to_discovery_context(
            target_url="https://example.com",
            http_data=http_data,
            http_client=mock_http_client,
        )
        assert context.crawl_data["js_contents"] == []

    def test_transform_to_network_requests_default_values(self) -> None:
        """기본값이 적용된 network_requests 변환"""
        transformer = DataTransformer()
        http_data: Dict[str, Any] = {
            "https://example.com/api": {
                "request": {"method": "GET"}  # 최소한의 request
            }
        }
        requests = transformer.transform_to_network_requests(http_data)
        assert len(requests) == 1
        assert requests[0]["method"] == "GET"
        assert requests[0]["headers"] == {}
        assert requests[0]["body"] is None
        assert requests[0]["post_data"] is None
        assert requests[0]["resource_type"] == ""
