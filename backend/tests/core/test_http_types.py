"""
Test HTTP Types - TypedDict 구조 검증

TDD RED Phase: HTTP 요청/응답 데이터 타입 정의 테스트
"""

from typing import get_type_hints, Optional, Union, Dict, Any


class TestHttpRequestDataType:
    """HttpRequestData TypedDict 구조 테스트"""

    def test_http_request_data_type_has_required_keys(self):
        """HttpRequestData가 method, headers, body 키를 가지는지 확인"""
        from app.types.http import HttpRequestData

        hints = get_type_hints(HttpRequestData)

        assert "method" in hints, "HttpRequestData should have 'method' key"
        assert "headers" in hints, "HttpRequestData should have 'headers' key"
        assert "body" in hints, "HttpRequestData should have 'body' key"

    def test_http_request_data_method_is_str(self):
        """method 필드가 str 타입인지 확인"""
        from app.types.http import HttpRequestData

        hints = get_type_hints(HttpRequestData)
        assert hints["method"] is str, "method should be str type"

    def test_http_request_data_headers_is_dict(self):
        """headers 필드가 Dict[str, str] 타입인지 확인"""
        from app.types.http import HttpRequestData

        hints = get_type_hints(HttpRequestData)
        # Dict[str, str] 체크
        assert hasattr(hints["headers"], "__origin__"), "headers should be a generic type"

    def test_http_request_data_body_is_optional(self):
        """body 필드가 Optional[str] 타입인지 확인"""
        from app.types.http import HttpRequestData

        hints = get_type_hints(HttpRequestData)
        # Optional[str] = Union[str, None]
        body_hint = hints["body"]
        assert hasattr(body_hint, "__origin__"), "body should be Optional type"


class TestHttpResponseDataType:
    """HttpResponseData TypedDict 구조 테스트"""

    def test_http_response_data_type_has_required_keys(self):
        """HttpResponseData가 status, headers, body 키를 가지는지 확인"""
        from app.types.http import HttpResponseData

        hints = get_type_hints(HttpResponseData)

        assert "status" in hints, "HttpResponseData should have 'status' key"
        assert "headers" in hints, "HttpResponseData should have 'headers' key"
        assert "body" in hints, "HttpResponseData should have 'body' key"

    def test_http_response_data_status_is_int(self):
        """status 필드가 int 타입인지 확인"""
        from app.types.http import HttpResponseData

        hints = get_type_hints(HttpResponseData)
        assert hints["status"] is int, "status should be int type"

    def test_http_response_data_body_accepts_multiple_types(self):
        """body 필드가 str, dict, None을 허용하는지 확인"""
        from app.types.http import HttpResponseData

        hints = get_type_hints(HttpResponseData)
        body_hint = hints["body"]
        # Optional[Union[str, dict]] 체크
        assert hasattr(body_hint, "__origin__"), "body should be Union/Optional type"


class TestHttpDataType:
    """HttpData TypedDict 구조 테스트"""

    def test_http_data_type_structure(self):
        """HttpData가 request, response, parameters 구조를 가지는지 확인"""
        from app.types.http import HttpData

        hints = get_type_hints(HttpData)

        assert "request" in hints, "HttpData should have 'request' key"
        assert "response" in hints, "HttpData should have 'response' key"
        assert "parameters" in hints, "HttpData should have 'parameters' key"

    def test_http_data_allows_partial_keys(self):
        """HttpData가 부분 키만 가질 수 있는지 확인 (total=False)"""
        from app.types.http import HttpData

        # total=False인 TypedDict는 __required_keys__가 비어있음
        required = getattr(HttpData, "__required_keys__", set())
        optional = getattr(HttpData, "__optional_keys__", set())

        # 모든 키가 optional이어야 함 (total=False)
        assert len(required) == 0, "HttpData should have no required keys (total=False)"
        assert len(optional) > 0, "HttpData should have optional keys"

    def test_http_data_request_is_http_request_data(self):
        """request 필드가 HttpRequestData 타입인지 확인"""
        from app.types.http import HttpData, HttpRequestData

        hints = get_type_hints(HttpData)
        assert hints["request"] is HttpRequestData, "request should be HttpRequestData type"

    def test_http_data_response_is_http_response_data(self):
        """response 필드가 HttpResponseData 타입인지 확인"""
        from app.types.http import HttpData, HttpResponseData

        hints = get_type_hints(HttpData)
        assert hints["response"] is HttpResponseData, "response should be HttpResponseData type"


class TestHttpTypesUsage:
    """HTTP 타입 실제 사용 테스트"""

    def test_create_valid_http_request_data(self):
        """유효한 HttpRequestData 인스턴스 생성"""
        from app.types.http import HttpRequestData

        request: HttpRequestData = {
            "method": "GET",
            "headers": {"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
            "body": None,
        }

        assert request["method"] == "GET"
        assert "User-Agent" in request["headers"]
        assert request["body"] is None

    def test_create_valid_http_response_data(self):
        """유효한 HttpResponseData 인스턴스 생성"""
        from app.types.http import HttpResponseData

        response: HttpResponseData = {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": {"key": "value"},
        }

        assert response["status"] == 200
        assert response["body"] == {"key": "value"}

    def test_create_valid_http_data(self):
        """유효한 HttpData 인스턴스 생성 (부분 키)"""
        from app.types.http import HttpData

        # request만 있는 경우 (total=False 이므로 가능)
        http_data: HttpData = {
            "request": {
                "method": "POST",
                "headers": {},
                "body": '{"data": "test"}',
            }
        }

        assert "request" in http_data
        assert http_data["request"]["method"] == "POST"

    def test_create_http_data_with_parameters(self):
        """parameters를 포함한 HttpData 생성"""
        from app.types.http import HttpData

        http_data: HttpData = {
            "parameters": {"page": "1", "sort": "desc"},
        }

        assert http_data["parameters"]["page"] == "1"


class TestParsedContentType:
    """ParsedContent TypedDict 구조 테스트"""

    def test_parsed_content_type_has_required_keys(self):
        """ParsedContent가 content_type, body, truncated, original_size 키를 가지는지 확인"""
        from app.types.http import ParsedContent

        hints = get_type_hints(ParsedContent)

        assert "content_type" in hints, "ParsedContent should have 'content_type' key"
        assert "body" in hints, "ParsedContent should have 'body' key"
        assert "truncated" in hints, "ParsedContent should have 'truncated' key"
        assert "original_size" in hints, "ParsedContent should have 'original_size' key"

    def test_parsed_content_content_type_is_str(self):
        """content_type 필드가 str 타입인지 확인"""
        from app.types.http import ParsedContent

        hints = get_type_hints(ParsedContent)
        assert hints["content_type"] is str, "content_type should be str type"

    def test_parsed_content_body_is_optional_str(self):
        """body 필드가 Optional[str] 타입인지 확인"""
        from app.types.http import ParsedContent

        hints = get_type_hints(ParsedContent)
        body_hint = hints["body"]
        # Optional[str] = Union[str, None]
        assert hasattr(body_hint, "__origin__"), "body should be Optional type"

    def test_parsed_content_truncated_is_bool(self):
        """truncated 필드가 bool 타입인지 확인"""
        from app.types.http import ParsedContent

        hints = get_type_hints(ParsedContent)
        assert hints["truncated"] is bool, "truncated should be bool type"


class TestParsedContentUsage:
    """ParsedContent 실제 사용 테스트"""

    def test_create_valid_parsed_content_with_body(self):
        """body가 있는 유효한 ParsedContent 인스턴스 생성"""
        from app.types.http import ParsedContent

        content: ParsedContent = {
            "content_type": "application/json",
            "body": '{"key": "value"}',
            "truncated": False,
            "original_size": 18,
        }

        assert content["content_type"] == "application/json"
        assert content["body"] == '{"key": "value"}'
        assert content["truncated"] is False
        assert content["original_size"] == 18

    def test_create_valid_parsed_content_with_none_body(self):
        """body가 None인 유효한 ParsedContent 인스턴스 생성"""
        from app.types.http import ParsedContent

        content: ParsedContent = {
            "content_type": "application/octet-stream",
            "body": None,
            "truncated": False,
            "original_size": 0,
        }

        assert content["body"] is None
        assert content["original_size"] == 0

    def test_create_truncated_parsed_content(self):
        """truncated=True인 ParsedContent 인스턴스 생성"""
        from app.types.http import ParsedContent

        content: ParsedContent = {
            "content_type": "text/html",
            "body": "<html>...",
            "truncated": True,
            "original_size": 1048576,
        }

        assert content["truncated"] is True
        assert content["original_size"] > len(content["body"] or "")

    def test_parsed_content_with_various_content_types(self):
        """다양한 content_type으로 ParsedContent 생성"""
        from app.types.http import ParsedContent

        for ct in ["application/json", "text/html; charset=utf-8", "image/png"]:
            content: ParsedContent = {
                "content_type": ct,
                "body": None,
                "truncated": False,
                "original_size": 0,
            }
            assert content["content_type"] == ct
