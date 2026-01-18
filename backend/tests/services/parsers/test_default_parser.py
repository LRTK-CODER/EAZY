"""DefaultResponseParser 테스트.

TDD RED Phase: 이 테스트들은 구현 전에 작성되어 실패해야 합니다.
"""

import logging

import pytest

from app.services.parsers.base import ResponseData


class TestDefaultResponseParserSupports:
    """DefaultResponseParser.supports() 메서드 테스트."""

    def test_supports_any_content_type(self):
        """모든 content-type에 True 반환."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        assert parser.supports("application/json") is True
        assert parser.supports("text/html") is True
        assert parser.supports("image/png") is True
        assert parser.supports("application/octet-stream") is True

    def test_supports_empty_string(self):
        """빈 문자열도 지원."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        assert parser.supports("") is True

    def test_supports_unknown_type(self):
        """알 수 없는 타입도 지원."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        assert parser.supports("application/x-unknown-type") is True
        assert parser.supports("custom/weird-format") is True


class TestDefaultResponseParserParse:
    """DefaultResponseParser.parse() 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_returns_parsed_content_type(self):
        """ParsedContent 구조 반환 확인."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/octet-stream",
            headers={},
            body=b"binary data",
        )

        result = await parser.parse(response)

        assert result is not None
        assert "content_type" in result
        assert "body" in result
        assert "truncated" in result
        assert "original_size" in result

    @pytest.mark.asyncio
    async def test_returns_none_body(self):
        """body 필드가 None."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/octet-stream",
            headers={},
            body=b"some binary content",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["body"] is None

    @pytest.mark.asyncio
    async def test_preserves_content_type(self):
        """content_type 필드가 원본 content-type 보존."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        content_type = "application/x-custom-type; charset=utf-8"
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type=content_type,
            headers={},
            body=b"data",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == content_type

    @pytest.mark.asyncio
    async def test_returns_original_size(self):
        """original_size가 원본 body 크기와 일치."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        body_data = b"0123456789" * 100  # 1000 bytes
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/octet-stream",
            headers={},
            body=body_data,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["original_size"] == 1000

    @pytest.mark.asyncio
    async def test_truncated_is_false(self):
        """truncated 항상 False (파싱하지 않으므로)."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/octet-stream",
            headers={},
            body=b"data",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_handles_empty_body(self):
        """빈 body 처리."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/octet-stream",
            headers={},
            body=b"",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["body"] is None
        assert result["original_size"] == 0

    @pytest.mark.asyncio
    async def test_logs_unknown_content_type(self, caplog):
        """알 수 없는 content-type 처리 시 INFO 로깅."""
        from app.services.parsers.default_parser import DefaultResponseParser

        parser = DefaultResponseParser()
        response = ResponseData(
            url="http://example.com/file.bin",
            status=200,
            content_type="application/x-unknown",
            headers={},
            body=b"data",
        )

        with caplog.at_level(logging.INFO):
            await parser.parse(response)

        assert len(caplog.records) >= 1
        log_message = caplog.records[0].message
        assert "application/x-unknown" in log_message
        assert "http://example.com/file.bin" in log_message


class TestDefaultResponseParserIntegration:
    """DefaultResponseParser Registry 통합 테스트."""

    def test_registry_returns_default_as_fallback(self):
        """Registry에서 fallback으로 DefaultResponseParser 반환."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.default_parser import DefaultResponseParser

        registry = ResponseParserRegistry()
        # 아무 파서도 등록하지 않음

        parser = registry.get_parser("application/x-unknown")

        assert isinstance(parser, DefaultResponseParser)

    def test_registry_uses_default_when_no_match(self):
        """등록된 파서가 매칭되지 않으면 DefaultResponseParser 사용."""
        from unittest.mock import MagicMock

        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.default_parser import DefaultResponseParser

        registry = ResponseParserRegistry()

        # JSON만 지원하는 mock 파서 등록
        mock_parser = MagicMock()
        mock_parser.supports = MagicMock(
            side_effect=lambda ct: "application/json" in ct
        )
        registry.register(mock_parser)

        # HTML 요청 -> DefaultResponseParser 반환
        parser = registry.get_parser("text/html")
        assert isinstance(parser, DefaultResponseParser)

    @pytest.mark.asyncio
    async def test_registry_default_parser_returns_parsed_content(self):
        """Registry의 default 파서가 ParsedContent 반환."""
        from app.services.parsers.base import ResponseParserRegistry

        registry = ResponseParserRegistry()
        parser = registry.get_parser("application/x-unknown")

        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="application/x-unknown",
            headers={},
            body=b"unknown data",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "application/x-unknown"
        assert result["body"] is None
