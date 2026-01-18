"""HtmlResponseParser 테스트.

TDD RED Phase: Phase 3.2 HtmlResponseParser 구현을 위한 테스트.
HTML, CSS, JavaScript 텍스트 콘텐츠 파싱을 검증합니다.
"""

import pytest

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData


class TestHtmlResponseParserSupports:
    """HtmlResponseParser.supports() 메서드 테스트."""

    def test_supports_text_html(self):
        """text/html Content-Type 지원 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("text/html") is True

    def test_supports_text_css(self):
        """text/css Content-Type 지원 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("text/css") is True

    def test_supports_text_javascript(self):
        """text/javascript Content-Type 지원 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("text/javascript") is True

    def test_supports_application_javascript(self):
        """application/javascript Content-Type 지원 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("application/javascript") is True

    def test_supports_content_type_with_charset(self):
        """charset 포함된 Content-Type 지원 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("text/html; charset=utf-8") is True
        assert parser.supports("text/css;charset=UTF-8") is True
        assert parser.supports("text/javascript; charset=iso-8859-1") is True

    def test_not_supports_application_json(self):
        """application/json은 지원하지 않음."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("application/json") is False

    def test_not_supports_image_types(self):
        """이미지 타입은 지원하지 않음."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        assert parser.supports("image/png") is False
        assert parser.supports("image/jpeg") is False
        assert parser.supports("image/gif") is False


class TestHtmlResponseParserParse:
    """HtmlResponseParser.parse() 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_parses_html_content(self):
        """HTML 콘텐츠 파싱."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        html_body = b"<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
        response = ResponseData(
            url="http://example.com/page.html",
            status=200,
            content_type="text/html",
            headers={"Content-Type": "text/html"},
            body=html_body,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "text/html"
        assert result["truncated"] is False
        assert "<h1>Hello</h1>" in result["body"]

    @pytest.mark.asyncio
    async def test_parses_css_content(self):
        """CSS 콘텐츠 파싱."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        css_body = b"body { background-color: #fff; } .container { max-width: 1200px; }"
        response = ResponseData(
            url="http://example.com/style.css",
            status=200,
            content_type="text/css",
            headers={"Content-Type": "text/css"},
            body=css_body,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "text/css"
        assert "background-color" in result["body"]
        assert ".container" in result["body"]

    @pytest.mark.asyncio
    async def test_parses_javascript_content(self):
        """JavaScript 콘텐츠 파싱."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        js_body = b"function hello() { console.log('Hello, World!'); }"
        response = ResponseData(
            url="http://example.com/script.js",
            status=200,
            content_type="text/javascript",
            headers={"Content-Type": "text/javascript"},
            body=js_body,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "text/javascript"
        assert "function hello()" in result["body"]

    @pytest.mark.asyncio
    async def test_truncates_large_body(self):
        """MAX_BODY_SIZE 초과 시 truncate."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()

        # MAX_BODY_SIZE보다 큰 HTML 생성
        large_content = "x" * (MAX_BODY_SIZE + 1000)
        large_html = f"<html><body>{large_content}</body></html>".encode("utf-8")

        response = ResponseData(
            url="http://example.com/large.html",
            status=200,
            content_type="text/html",
            headers={},
            body=large_html,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["truncated"] is True
        assert len(result["body"]) <= MAX_BODY_SIZE + len("... [TRUNCATED]")
        assert result["body"].endswith("... [TRUNCATED]")
        assert result["original_size"] == len(large_html)

    @pytest.mark.asyncio
    async def test_handles_empty_body(self):
        """빈 body 처리."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        response = ResponseData(
            url="http://example.com/empty.html",
            status=200,
            content_type="text/html",
            headers={},
            body=b"",
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["body"] == ""
        assert result["original_size"] == 0
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_returns_parsed_content_type(self):
        """반환 타입이 ParsedContent 구조인지 확인."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        response = ResponseData(
            url="http://example.com/test.html",
            status=200,
            content_type="text/html; charset=utf-8",
            headers={},
            body=b"<html><body>Test</body></html>",
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
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        body = b"<html><body>Hello World</body></html>"
        response = ResponseData(
            url="http://example.com/test.html",
            status=200,
            content_type="text/html",
            headers={},
            body=body,
        )

        result = await parser.parse(response)

        assert result["original_size"] == len(body)

    @pytest.mark.asyncio
    async def test_handles_unicode_content(self):
        """유니코드 콘텐츠 처리."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        response = ResponseData(
            url="http://example.com/korean.html",
            status=200,
            content_type="text/html; charset=utf-8",
            headers={},
            body="<html><body>한글 테스트 🚀</body></html>".encode("utf-8"),
        )

        result = await parser.parse(response)

        assert result is not None
        assert "한글 테스트" in result["body"]
        assert "🚀" in result["body"]

    @pytest.mark.asyncio
    async def test_handles_decode_error(self):
        """잘못된 인코딩 처리."""
        from app.services.parsers.html_parser import HtmlResponseParser

        parser = HtmlResponseParser()
        # 잘못된 UTF-8 바이트 시퀀스
        invalid_bytes = b"<html>\xff\xfe</html>"
        response = ResponseData(
            url="http://example.com/invalid.html",
            status=200,
            content_type="text/html",
            headers={},
            body=invalid_bytes,
        )

        result = await parser.parse(response)

        # 예외 없이 처리되어야 함
        assert result is not None
        assert result["content_type"] == "text/html"


class TestHtmlResponseParserIntegration:
    """HtmlResponseParser와 Registry 통합 테스트."""

    def test_can_register_to_registry(self):
        """Registry에 등록 가능한지 확인."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.html_parser import HtmlResponseParser

        registry = ResponseParserRegistry()
        parser = HtmlResponseParser()

        # 예외 없이 등록 가능해야 함
        registry.register(parser)

        # 등록 후 HTML 타입에 대해 반환
        result = registry.get_parser("text/html")
        assert result is parser

    @pytest.mark.asyncio
    async def test_registry_delegates_to_html_parser(self):
        """Registry가 HTML 파싱을 HtmlResponseParser에 위임."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.html_parser import HtmlResponseParser

        registry = ResponseParserRegistry()
        registry.register(HtmlResponseParser())

        parser = registry.get_parser("text/html; charset=utf-8")
        response = ResponseData(
            url="http://example.com",
            status=200,
            content_type="text/html; charset=utf-8",
            headers={},
            body=b"<html><body>Registered</body></html>",
        )

        result = await parser.parse(response)

        assert result is not None
        assert "Registered" in result["body"]

    def test_registry_returns_html_parser_for_css(self):
        """Registry가 CSS 타입에 HtmlResponseParser 반환."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.html_parser import HtmlResponseParser

        registry = ResponseParserRegistry()
        parser = HtmlResponseParser()
        registry.register(parser)

        result = registry.get_parser("text/css")
        assert result is parser

    def test_registry_returns_html_parser_for_javascript(self):
        """Registry가 JavaScript 타입에 HtmlResponseParser 반환."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.html_parser import HtmlResponseParser

        registry = ResponseParserRegistry()
        parser = HtmlResponseParser()
        registry.register(parser)

        result = registry.get_parser("application/javascript")
        assert result is parser
