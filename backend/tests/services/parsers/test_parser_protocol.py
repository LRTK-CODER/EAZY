"""ResponseParser Protocol 및 Registry 테스트.

TDD RED Phase: 이 테스트들은 구현 전에 작성되어 실패해야 합니다.
"""

import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestResponseParserProtocol:
    """ResponseParser Protocol 정의 테스트."""

    def test_response_parser_has_supports_method(self):
        """supports() 메서드가 정의되어 있는지 확인."""
        from app.services.parsers.base import ResponseParser

        assert "supports" in dir(ResponseParser)

    def test_response_parser_has_parse_method(self):
        """parse() 메서드가 정의되어 있는지 확인."""
        from app.services.parsers.base import ResponseParser

        assert "parse" in dir(ResponseParser)

    def test_parse_method_is_async(self):
        """parse()가 async 함수인지 확인."""
        from app.services.parsers.base import ResponseParser

        assert inspect.iscoroutinefunction(ResponseParser.parse)

    def test_supports_has_content_type_parameter(self):
        """supports()가 content_type 파라미터를 받는지 확인."""
        from app.services.parsers.base import ResponseParser

        sig = inspect.signature(ResponseParser.supports)
        assert "content_type" in sig.parameters

    def test_parse_has_response_parameter(self):
        """parse()가 response 파라미터를 받는지 확인."""
        from app.services.parsers.base import ResponseParser

        sig = inspect.signature(ResponseParser.parse)
        assert "response" in sig.parameters


class TestResponseParserRegistry:
    """ResponseParserRegistry 동작 테스트."""

    def test_registry_has_register_method(self):
        """register() 메서드가 존재하는지 확인."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()
        assert hasattr(registry, "register")
        assert callable(registry.register)

    def test_registry_has_get_parser_method(self):
        """get_parser() 메서드가 존재하는지 확인."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()
        assert hasattr(registry, "get_parser")
        assert callable(registry.get_parser)

    def test_parser_registry_get_parser_returns_parser(self):
        """등록된 파서를 정확히 반환하는지 확인."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()

        # Mock 파서 생성
        mock_parser = MagicMock()
        mock_parser.supports = MagicMock(return_value=True)

        registry.register(mock_parser)
        result = registry.get_parser("application/json")

        assert result is mock_parser

    def test_parser_registry_returns_default_for_unknown(self):
        """알 수 없는 content-type에 대해 default 파서 반환."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()
        parser = registry.get_parser("application/unknown-type")

        # Default 파서는 모든 타입 지원
        assert parser.supports("application/unknown-type") is True

    def test_registry_respects_parser_order(self):
        """파서 등록 순서대로 검색하는지 확인."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()

        # 첫 번째 파서: json만 지원
        first_parser = MagicMock()
        first_parser.supports = MagicMock(side_effect=lambda ct: "json" in ct)

        # 두 번째 파서: 모든 것 지원
        second_parser = MagicMock()
        second_parser.supports = MagicMock(return_value=True)

        registry.register(first_parser)
        registry.register(second_parser)

        # json은 첫 번째 파서가 처리
        result = registry.get_parser("application/json")
        assert result is first_parser

        # html은 두 번째 파서가 처리
        result = registry.get_parser("text/html")
        assert result is second_parser

    def test_registry_multiple_parsers_same_type(self):
        """여러 파서가 같은 타입 지원 시 첫 번째 반환."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()

        parser1 = MagicMock()
        parser1.supports = MagicMock(return_value=True)

        parser2 = MagicMock()
        parser2.supports = MagicMock(return_value=True)

        registry.register(parser1)
        registry.register(parser2)

        result = registry.get_parser("text/plain")
        assert result is parser1  # 첫 번째 등록된 파서


class TestResponseData:
    """ResponseData 구조 테스트."""

    def test_response_data_has_required_fields(self):
        """필수 필드가 존재하는지 확인."""
        from app.services.parsers.base import ResponseData

        data = ResponseData(
            url="http://example.com",
            status=200,
            content_type="text/html",
            headers={"Content-Type": "text/html"},
            body=b"<html></html>",
        )

        assert data.url == "http://example.com"
        assert data.status == 200
        assert data.content_type == "text/html"
        assert data.headers == {"Content-Type": "text/html"}
        assert data.body == b"<html></html>"

    def test_response_data_is_immutable(self):
        """ResponseData가 불변(frozen)인지 확인."""
        from app.services.parsers.base import ResponseData
        from dataclasses import FrozenInstanceError

        data = ResponseData(
            url="http://example.com",
            status=200,
            content_type="text/html",
            headers={},
            body=b"",
        )

        with pytest.raises(FrozenInstanceError):
            data.url = "http://other.com"

    def test_response_data_body_is_bytes(self):
        """body 필드가 bytes 타입인지 확인."""
        from app.services.parsers.base import ResponseData

        data = ResponseData(
            url="http://example.com",
            status=200,
            content_type="text/plain",
            headers={},
            body=b"test content",
        )

        assert isinstance(data.body, bytes)


class TestMockParserCompliance:
    """Mock 파서가 Protocol을 만족하는지 확인."""

    @pytest.mark.asyncio
    async def test_mock_parser_can_be_used_as_response_parser(self):
        """Mock 객체가 ResponseParser처럼 사용 가능한지 확인."""
        mock_parser = MagicMock()
        mock_parser.supports = MagicMock(return_value=True)
        mock_parser.parse = AsyncMock(return_value={"key": "value"})

        # Protocol 준수 확인
        assert mock_parser.supports("application/json") is True
        result = await mock_parser.parse(MagicMock())
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_custom_parser_class_satisfies_protocol(self):
        """커스텀 파서 클래스가 Protocol을 만족하는지 확인."""
        from app.services.parsers.base import ResponseData

        class CustomParser:
            """테스트용 커스텀 파서."""

            def supports(self, content_type: str) -> bool:
                return "custom" in content_type

            async def parse(self, response: ResponseData):
                return {"custom": True}

        parser = CustomParser()
        assert parser.supports("application/custom") is True
        assert parser.supports("application/json") is False

        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/custom",
            headers={},
            body=b"{}",
        )
        result = await parser.parse(response)
        assert result == {"custom": True}


class TestContentTypeEdgeCases:
    """Content-Type 엣지 케이스 테스트."""

    def test_registry_handles_empty_content_type(self):
        """빈 content-type 처리."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()
        parser = registry.get_parser("")

        # Default 파서 반환
        assert parser.supports("") is True

    def test_registry_handles_content_type_with_charset(self):
        """charset 포함된 content-type 처리."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()

        mock_parser = MagicMock()
        # 실제 파서처럼 부분 매칭
        mock_parser.supports = MagicMock(
            side_effect=lambda ct: "application/json" in ct
        )

        registry.register(mock_parser)

        # charset 포함된 content-type도 매칭
        result = registry.get_parser("application/json; charset=utf-8")
        assert result is mock_parser
