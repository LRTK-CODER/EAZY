"""ImageResponseParser 테스트.

TDD RED Phase: Phase 3.3 ImageResponseParser 구현을 위한 테스트.
이미지 Content-Type을 Base64로 인코딩하여 처리합니다.
"""

import base64

import pytest

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData


class TestImageResponseParserSupports:
    """ImageResponseParser.supports() 메서드 테스트."""

    def test_supports_image_png(self):
        """image/png Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/png") is True

    def test_supports_image_jpeg(self):
        """image/jpeg Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/jpeg") is True

    def test_supports_image_gif(self):
        """image/gif Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/gif") is True

    def test_supports_image_webp(self):
        """image/webp Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/webp") is True

    def test_supports_image_svg_xml(self):
        """image/svg+xml Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/svg+xml") is True

    def test_supports_image_x_icon(self):
        """image/x-icon (favicon) Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/x-icon") is True

    def test_supports_image_bmp(self):
        """image/bmp Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/bmp") is True

    def test_supports_image_tiff(self):
        """image/tiff Content-Type 지원 확인."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("image/tiff") is True

    def test_not_supports_text_html(self):
        """text/html은 지원하지 않음."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("text/html") is False

    def test_not_supports_application_json(self):
        """application/json은 지원하지 않음."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("application/json") is False

    def test_not_supports_text_css(self):
        """text/css는 지원하지 않음."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        assert parser.supports("text/css") is False


class TestImageResponseParserParse:
    """ImageResponseParser.parse() 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_encodes_png_to_base64(self):
        """PNG 바이너리를 Base64로 인코딩."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        # 1x1 투명 PNG (최소 유효 PNG)
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        response = ResponseData(
            url="http://example.com/image.png",
            status=200,
            content_type="image/png",
            headers={"Content-Type": "image/png"},
            body=png_bytes,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "image/png"
        assert result["truncated"] is False
        # Base64로 인코딩되었는지 확인 (디코딩 가능해야 함)
        decoded = base64.b64decode(result["body"])
        assert decoded == png_bytes

    @pytest.mark.asyncio
    async def test_encodes_jpeg_to_base64(self):
        """JPEG 바이너리를 Base64로 인코딩."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        # 임의의 바이너리 데이터 (JPEG 시그니처)
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        response = ResponseData(
            url="http://example.com/image.jpg",
            status=200,
            content_type="image/jpeg",
            headers={"Content-Type": "image/jpeg"},
            body=jpeg_bytes,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "image/jpeg"
        decoded = base64.b64decode(result["body"])
        assert decoded == jpeg_bytes

    @pytest.mark.asyncio
    async def test_truncates_large_image(self):
        """MAX_BODY_SIZE 초과 시 바이너리를 먼저 truncate."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()

        # MAX_BODY_SIZE보다 큰 이미지 데이터 생성
        large_image = b"\x89PNG" + b"\x00" * (MAX_BODY_SIZE + 1000)

        response = ResponseData(
            url="http://example.com/large.png",
            status=200,
            content_type="image/png",
            headers={},
            body=large_image,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["truncated"] is True
        assert result["original_size"] == len(large_image)

        # Base64 디코딩 후 크기가 MAX_BODY_SIZE 이하인지 확인
        decoded = base64.b64decode(result["body"])
        assert len(decoded) <= MAX_BODY_SIZE

    @pytest.mark.asyncio
    async def test_handles_empty_body(self):
        """빈 body 처리."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        response = ResponseData(
            url="http://example.com/empty.png",
            status=200,
            content_type="image/png",
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
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        response = ResponseData(
            url="http://example.com/test.gif",
            status=200,
            content_type="image/gif",
            headers={},
            body=b"GIF89a\x01\x00\x01\x00\x00\x00\x00;",
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
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        body = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        response = ResponseData(
            url="http://example.com/test.png",
            status=200,
            content_type="image/png",
            headers={},
            body=body,
        )

        result = await parser.parse(response)

        assert result["original_size"] == len(body)

    @pytest.mark.asyncio
    async def test_handles_binary_data(self):
        """다양한 바이너리 데이터 정상 처리."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        # 모든 바이트 값을 포함하는 데이터
        binary_data = bytes(range(256))
        response = ResponseData(
            url="http://example.com/binary.png",
            status=200,
            content_type="image/png",
            headers={},
            body=binary_data,
        )

        result = await parser.parse(response)

        assert result is not None
        # Base64 디코딩 후 원본과 일치하는지 확인
        decoded = base64.b64decode(result["body"])
        assert decoded == binary_data

    @pytest.mark.asyncio
    async def test_handles_svg_as_base64(self):
        """SVG도 Base64로 인코딩."""
        from app.services.parsers.image_parser import ImageResponseParser

        parser = ImageResponseParser()
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="50"/></svg>'
        response = ResponseData(
            url="http://example.com/icon.svg",
            status=200,
            content_type="image/svg+xml",
            headers={},
            body=svg_content,
        )

        result = await parser.parse(response)

        assert result is not None
        assert result["content_type"] == "image/svg+xml"
        # Base64 디코딩 후 원본과 일치
        decoded = base64.b64decode(result["body"])
        assert decoded == svg_content


class TestImageResponseParserIntegration:
    """ImageResponseParser와 Registry 통합 테스트."""

    def test_can_register_to_registry(self):
        """Registry에 등록 가능한지 확인."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.image_parser import ImageResponseParser

        registry = ResponseParserRegistry()
        parser = ImageResponseParser()

        # 예외 없이 등록 가능해야 함
        registry.register(parser)

        # 등록 후 이미지 타입에 대해 반환
        result = registry.get_parser("image/png")
        assert result is parser

    @pytest.mark.asyncio
    async def test_registry_delegates_to_image_parser(self):
        """Registry가 이미지 파싱을 ImageResponseParser에 위임."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.image_parser import ImageResponseParser

        registry = ResponseParserRegistry()
        registry.register(ImageResponseParser())

        parser = registry.get_parser("image/jpeg")
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        response = ResponseData(
            url="http://example.com/photo.jpg",
            status=200,
            content_type="image/jpeg",
            headers={},
            body=jpeg_bytes,
        )

        result = await parser.parse(response)

        assert result is not None
        decoded = base64.b64decode(result["body"])
        assert decoded == jpeg_bytes

    def test_registry_returns_image_parser_for_webp(self):
        """Registry가 WebP 타입에 ImageResponseParser 반환."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.image_parser import ImageResponseParser

        registry = ResponseParserRegistry()
        parser = ImageResponseParser()
        registry.register(parser)

        result = registry.get_parser("image/webp")
        assert result is parser

    def test_registry_returns_image_parser_for_svg(self):
        """Registry가 SVG 타입에 ImageResponseParser 반환."""
        from app.services.parsers.base import ResponseParserRegistry
        from app.services.parsers.image_parser import ImageResponseParser

        registry = ResponseParserRegistry()
        parser = ImageResponseParser()
        registry.register(parser)

        result = registry.get_parser("image/svg+xml")
        assert result is parser
