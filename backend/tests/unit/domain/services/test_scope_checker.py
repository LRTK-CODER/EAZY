"""Unit tests for ScopeChecker domain service."""

from app.domain.services.scope_checker import ScopeChecker
from app.models.target import TargetScope


class MockTarget:
    """Test용 Target mock"""

    def __init__(self, url: str, scope: TargetScope):
        self.url = url
        self.scope = scope


class TestScopeChecker:
    """ScopeChecker unit tests (wraps existing ScopeFilter)."""

    def test_domain_scope_allows_same_domain(self):
        """DOMAIN scope: 같은 도메인 허용 (www 동일 취급)"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
        assert checker.is_in_scope("https://example.com/page", target) is True
        assert checker.is_in_scope("https://www.example.com/page", target) is True

    def test_domain_scope_blocks_subdomains(self):
        """DOMAIN scope: 서브도메인은 차단"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
        assert checker.is_in_scope("https://api.example.com/", target) is False

    def test_domain_scope_blocks_different_domain(self):
        """DOMAIN scope: 다른 도메인 차단"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
        assert checker.is_in_scope("https://evil.com/", target) is False

    def test_subdomain_scope_allows_subdomains(self):
        """SUBDOMAIN scope: 같은 base domain의 모든 서브도메인 허용"""
        checker = ScopeChecker()
        target = MockTarget(url="https://www.example.com", scope=TargetScope.SUBDOMAIN)
        assert checker.is_in_scope("https://www.example.com/page", target) is True
        assert checker.is_in_scope("https://api.example.com/", target) is True
        assert checker.is_in_scope("https://example.com/", target) is True

    def test_subdomain_scope_blocks_different_domain(self):
        """SUBDOMAIN scope: 다른 base domain 차단"""
        checker = ScopeChecker()
        target = MockTarget(url="https://www.example.com", scope=TargetScope.SUBDOMAIN)
        assert checker.is_in_scope("https://evil.com/", target) is False

    def test_url_only_scope_allows_same_url_prefix(self):
        """URL_ONLY scope: 같은 URL prefix만 허용"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com/app", scope=TargetScope.URL_ONLY)
        assert checker.is_in_scope("https://example.com/app/page", target) is True
        assert checker.is_in_scope("https://example.com/app", target) is True

    def test_url_only_scope_blocks_different_path(self):
        """URL_ONLY scope: 다른 path 차단"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com/app", scope=TargetScope.URL_ONLY)
        assert checker.is_in_scope("https://example.com/other", target) is False

    def test_handles_none_url(self):
        """None URL 처리"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
        assert checker.is_in_scope(None, target) is False

    def test_handles_none_target(self):
        """None target 처리"""
        checker = ScopeChecker()
        assert checker.is_in_scope("https://example.com/", None) is False

    def test_filter_urls(self):
        """URL 목록 필터링"""
        checker = ScopeChecker()
        target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
        urls = [
            "https://example.com/page1",
            "https://evil.com/",
            "https://example.com/page2",
        ]
        filtered = checker.filter_urls(urls, target)
        assert len(filtered) == 2
        assert "https://evil.com/" not in filtered
