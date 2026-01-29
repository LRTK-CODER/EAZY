"""Unit tests for UrlValidator."""

from app.domain.services.url_validator import UrlValidator


class TestUrlValidator:
    """UrlValidator unit tests."""

    def test_blocks_localhost(self):
        """localhost 차단"""
        validator = UrlValidator()
        assert validator.is_safe("http://localhost/") is False
        assert validator.is_safe("http://127.0.0.1/") is False

    def test_blocks_private_ip_ranges(self):
        """Private IP 대역 차단"""
        validator = UrlValidator()
        assert validator.is_safe("http://10.0.0.1/") is False
        assert validator.is_safe("http://192.168.1.1/") is False
        assert validator.is_safe("http://172.16.0.1/") is False

    def test_blocks_link_local(self):
        """Link-local 주소 차단 (AWS metadata)"""
        validator = UrlValidator()
        assert validator.is_safe("http://169.254.1.1/") is False
        assert validator.is_safe("http://169.254.169.254/") is False

    def test_blocks_dangerous_schemes(self):
        """위험한 스킴 차단"""
        validator = UrlValidator()
        assert validator.is_safe("file:///etc/passwd") is False
        assert validator.is_safe("gopher://evil.com/") is False
        assert validator.is_safe("data:text/html,<script>") is False
        assert validator.is_safe("ftp://ftp.example.com/") is False

    def test_allows_valid_public_urls(self):
        """유효한 공개 URL 허용"""
        validator = UrlValidator()
        assert validator.is_safe("https://example.com/") is True
        assert validator.is_safe("https://api.github.com/") is True
        assert validator.is_safe("http://example.com/page") is True

    def test_blocks_ipv6_localhost(self):
        """IPv6 localhost 차단"""
        validator = UrlValidator()
        assert validator.is_safe("http://[::1]/") is False

    def test_handles_none_and_empty(self):
        """None 및 빈 문자열 처리"""
        validator = UrlValidator()
        assert validator.is_safe(None) is False
        assert validator.is_safe("") is False

    def test_handles_malformed_urls(self):
        """잘못된 형식의 URL 처리"""
        validator = UrlValidator()
        assert validator.is_safe("not-a-url") is False
        assert validator.is_safe("://missing-scheme") is False
        assert validator.is_safe("https://") is False

    def test_validate_returns_result_with_reason(self):
        """validate()는 ValidationResult 반환"""
        validator = UrlValidator()
        result = validator.validate("http://127.0.0.1/")
        assert result.is_safe is False
        assert "loopback" in result.reason.lower() or "blocked" in result.reason.lower()

        result = validator.validate("https://example.com/")
        assert result.is_safe is True
