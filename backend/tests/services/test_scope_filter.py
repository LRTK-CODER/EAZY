"""
Tests for ScopeFilter service.

TDD Red Phase: All tests should FAIL initially until implementation.
"""

from app.models.target import TargetScope
from app.services.scope_filter import ScopeFilter, extract_base_domain


class TestExtractBaseDomain:
    """Tests for extract_base_domain helper function."""

    def test_extract_base_domain_simple(self):
        """Given: example.com, When: extract, Then: example.com"""
        result = extract_base_domain("example.com")
        assert result == "example.com"

    def test_extract_base_domain_with_subdomain(self):
        """Given: api.example.com, When: extract, Then: example.com"""
        result = extract_base_domain("api.example.com")
        assert result == "example.com"

    def test_extract_base_domain_with_www(self):
        """Given: www.example.com, When: extract, Then: example.com"""
        result = extract_base_domain("www.example.com")
        assert result == "example.com"

    def test_extract_base_domain_nested_subdomain(self):
        """Given: a.b.c.example.com, When: extract, Then: example.com"""
        result = extract_base_domain("a.b.c.example.com")
        assert result == "example.com"

    def test_extract_base_domain_cctld(self):
        """Given: www.example.co.uk, When: extract, Then: example.co.uk"""
        result = extract_base_domain("www.example.co.uk")
        assert result == "example.co.uk"

    def test_extract_base_domain_invalid_returns_empty(self):
        """Given: invalid hostname, When: extract, Then: empty string"""
        result = extract_base_domain("invalid")
        assert result == ""


class TestScopeFilterDomainScope:
    """Tests for ScopeFilter with DOMAIN scope."""

    def test_domain_scope_allows_same_domain(self):
        """DOMAIN: example.com -> example.com/page allowed"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://example.com/page") is True

    def test_domain_scope_allows_www_variant(self):
        """DOMAIN: example.com -> www.example.com/page allowed (www equivalent)"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://www.example.com/page") is True

    def test_domain_scope_allows_www_to_naked(self):
        """DOMAIN: www.example.com -> example.com/page allowed"""
        scope_filter = ScopeFilter("https://www.example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://example.com/page") is True

    def test_domain_scope_blocks_subdomain(self):
        """DOMAIN: example.com -> api.example.com blocked"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://api.example.com") is False

    def test_domain_scope_blocks_different_domain(self):
        """DOMAIN: example.com -> other.com blocked"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://other.com/page") is False

    def test_domain_scope_blocks_similar_domain(self):
        """DOMAIN: example.com -> notexample.com blocked"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://notexample.com") is False


class TestScopeFilterSubdomainScope:
    """Tests for ScopeFilter with SUBDOMAIN scope."""

    def test_subdomain_scope_allows_same_subdomain(self):
        """SUBDOMAIN: api.example.com -> api.example.com/page allowed"""
        scope_filter = ScopeFilter("https://api.example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("https://api.example.com/page") is True

    def test_subdomain_scope_allows_different_subdomain(self):
        """SUBDOMAIN: www.example.com -> api.example.com allowed"""
        scope_filter = ScopeFilter("https://www.example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("https://api.example.com/page") is True

    def test_subdomain_scope_allows_naked_domain(self):
        """SUBDOMAIN: api.example.com -> example.com allowed"""
        scope_filter = ScopeFilter("https://api.example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("https://example.com/page") is True

    def test_subdomain_scope_allows_nested_subdomain(self):
        """SUBDOMAIN: example.com -> a.b.c.example.com allowed"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("https://a.b.c.example.com") is True

    def test_subdomain_scope_blocks_different_domain(self):
        """SUBDOMAIN: example.com -> other.com blocked"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("https://other.com") is False


class TestScopeFilterUrlOnlyScope:
    """Tests for ScopeFilter with URL_ONLY scope."""

    def test_url_only_scope_allows_same_path(self):
        """URL_ONLY: example.com/app -> example.com/app/sub allowed"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app/sub") is True

    def test_url_only_scope_allows_exact_path(self):
        """URL_ONLY: example.com/app -> example.com/app allowed"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app") is True

    def test_url_only_scope_blocks_different_path(self):
        """URL_ONLY: example.com/app -> example.com/other blocked"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/other") is False

    def test_url_only_scope_blocks_sibling_path(self):
        """URL_ONLY: example.com/app -> example.com/app2 blocked"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app2") is False

    def test_url_only_scope_blocks_parent_path(self):
        """URL_ONLY: example.com/app/sub -> example.com/app blocked"""
        scope_filter = ScopeFilter("https://example.com/app/sub", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app") is False

    def test_url_only_scope_blocks_different_domain(self):
        """URL_ONLY: example.com/app -> other.com/app blocked"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://other.com/app") is False


class TestScopeFilterBatchFiltering:
    """Tests for filter_urls batch method."""

    def test_filter_urls_returns_in_scope_only(self):
        """Filter multiple URLs -> return in-scope only"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        urls = [
            "https://example.com/page1",
            "https://api.example.com/api",  # out of scope
            "https://example.com/page2",
            "https://other.com/page",  # out of scope
            "https://www.example.com/page",  # in scope (www)
        ]
        result = scope_filter.filter_urls(urls)
        assert result == [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://www.example.com/page",
        ]

    def test_filter_urls_empty_list(self):
        """Empty list -> empty list"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        result = scope_filter.filter_urls([])
        assert result == []

    def test_filter_urls_all_out_of_scope(self):
        """All out-of-scope -> empty list"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        urls = ["https://other.com/page", "https://another.com/page"]
        result = scope_filter.filter_urls(urls)
        assert result == []


class TestScopeFilterEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_handles_url_with_port(self):
        """URL with port handling"""
        scope_filter = ScopeFilter("https://example.com:8443", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("https://example.com:8443/page") is True

    def test_handles_url_with_query_params(self):
        """URL with query params"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app?id=123") is True

    def test_handles_url_with_fragment(self):
        """URL with fragment"""
        scope_filter = ScopeFilter("https://example.com/app", TargetScope.URL_ONLY)
        assert scope_filter.is_in_scope("https://example.com/app#section") is True

    def test_handles_invalid_url_returns_false(self):
        """Invalid URL -> False"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("not-a-valid-url") is False

    def test_handles_empty_url_returns_false(self):
        """Empty URL -> False"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("") is False

    def test_handles_none_url_returns_false(self):
        """None URL -> False"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope(None) is False  # type: ignore


class TestScopeFilterProtocol:
    """Tests for protocol-agnostic behavior."""

    def test_http_and_https_treated_same(self):
        """HTTP and HTTPS treated the same"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.DOMAIN)
        assert scope_filter.is_in_scope("http://example.com/page") is True

    def test_https_target_with_http_url(self):
        """HTTPS target, HTTP URL also allowed"""
        scope_filter = ScopeFilter("https://example.com", TargetScope.SUBDOMAIN)
        assert scope_filter.is_in_scope("http://api.example.com") is True
