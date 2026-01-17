"""JsonResponseParser 테스트.

TDD RED Phase: Phase 3.1 JsonResponseParser 구현을 위한 테스트.
"""

import pytest

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData
from app.types.http import ParsedContent


class TestJsonResponseParserSupports:
    """JsonResponseParser.supports() 메서드 테스트."""

    def test_supports_application_json(self):
        """application/json Content-Type 지원 확인."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        assert parser.supports("application/json") is True

    def test_supports_application_json_with_charset(self):
        """charset 포함된 application/json 지원 확인."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        assert parser.supports("application/json; charset=utf-8") is True
        assert parser.supports("application/json;charset=UTF-8") is True

    def test_not_supports_text_html(self):
        """text/html은 지원하지 않음."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        assert parser.supports("text/html") is False

    def test_not_supports_image_types(self):
        """이미지 타입은 지원하지 않음."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        assert parser.supports("image/png") is False
        assert parser.supports("image/jpeg") is False


class TestJsonResponseParserParse:
    """JsonResponseParser.parse() 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_parses_valid_json_object(self):
        """유효한 JSON 객체 파싱."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={"Content-Type": "application/json"},
            body=b'{"key": "value", "number": 42}',
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "application/json"
        assert result["truncated"] is False
        assert '"key"' in result["body"]
        assert '"value"' in result["body"]

    @pytest.mark.asyncio
    async def test_parses_valid_json_array(self):
        """유효한 JSON 배열 파싱."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=b'[1, 2, 3, "test"]',
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["truncated"] is False
        assert "[1, 2, 3" in result["body"]

    @pytest.mark.asyncio
    async def test_handles_invalid_json_returns_original_text(self):
        """잘못된 JSON은 원본 텍스트 반환."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        invalid_json = b'{"key": "value", invalid}'
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=invalid_json,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "application/json"
        # 원본 텍스트가 그대로 반환되어야 함
        assert result["body"] == invalid_json.decode("utf-8")
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_truncates_large_body(self):
        """MAX_BODY_SIZE 초과 시 truncate."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()

        # MAX_BODY_SIZE보다 큰 JSON 생성
        large_value = "x" * (MAX_BODY_SIZE + 1000)
        large_json = f'{{"data": "{large_value}"}}'.encode("utf-8")

        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=large_json,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["truncated"] is True
        assert len(result["body"]) <= MAX_BODY_SIZE + len("... [TRUNCATED]")
        assert result["body"].endswith("... [TRUNCATED]")
        assert result["original_size"] == len(large_json)

    @pytest.mark.asyncio
    async def test_returns_parsed_content_type(self):
        """반환 타입이 ParsedContent 구조인지 확인."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=b'{"test": true}',
        )

        result = await parser.parse(response)

        # ParsedContent 필수 키 확인
        assert "content_type" in result
        assert "body" in result
        assert "truncated" in result
        assert "original_size" in result

        # 타입 확인
        assert isinstance(result["content_type"], str)
        assert isinstance(result["body"], str) or result["body"] is None
        assert isinstance(result["truncated"], bool)
        assert isinstance(result["original_size"], int)

    @pytest.mark.asyncio
    async def test_original_size_correct(self):
        """original_size가 원본 바이트 크기와 일치."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        body = b'{"key": "value"}'
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=body,
        )

        result = await parser.parse(response)

        assert result["original_size"] == len(body)

    @pytest.mark.asyncio
    async def test_parses_unicode_json(self):
        """유니코드 JSON 파싱."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body='{"message": "한글 테스트", "emoji": "🚀"}'.encode("utf-8"),
        )

        result = await parser.parse(response)

        assert result is not None
        assert "한글 테스트" in result["body"]
        assert "🚀" in result["body"]

    @pytest.mark.asyncio
    async def test_handles_empty_body(self):
        """빈 body 처리."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=b"",
        )

        result = await parser.parse(response)

        # 빈 body는 파싱 불가, 원본 반환
        assert result is not None
        assert result["body"] == ""
        assert result["original_size"] == 0

    @pytest.mark.asyncio
    async def test_parses_nested_json(self):
        """중첩된 JSON 구조 파싱."""
        from app.services.parsers.json_parser import JsonResponseParser

        parser = JsonResponseParser()
        nested_json = b'{"outer": {"inner": {"deep": [1, 2, 3]}}}'
        response = ResponseData(
            url="http://example.com/api",
            status=200,
            content_type="application/json",
            headers={},
            body=nested_json,
        )

        result = await parser.parse(response)

        assert result is not None
        assert "outer" in result["body"]
        assert "inner" in result["body"]
        assert "deep" in result["body"]


class TestJsonResponseParserIntegration:
    """JsonResponseParser와 Registry 통합 테스트."""

    def test_can_register_to_registry(self):
        """Registry에 등록 가능한지 확인."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.json_parser import JsonResponseParser

        registry = ResponseParserRegistry()
        parser = JsonResponseParser()

        # 예외 없이 등록 가능해야 함
        registry.register(parser)

        # 등록 후 JSON 타입에 대해 반환
        result = registry.get_parser("application/json")
        assert result is parser

    @pytest.mark.asyncio
    async def test_registry_delegates_to_json_parser(self):
        """Registry가 JSON 파싱을 JsonResponseParser에 위임."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.json_parser import JsonResponseParser

        registry = ResponseParserRegistry()
        registry.register(JsonResponseParser())

        parser = registry.get_parser("application/json; charset=utf-8")
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/json; charset=utf-8",
            headers={},
            body=b'{"registered": true}',
        )

        result = await parser.parse(response)

        assert result is not None
        assert "registered" in result["body"]
