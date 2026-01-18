"""
Tests for URL normalization service.

TDD Red Phase: All tests should FAIL initially.
"""

import pytest

from app.services.url_normalizer import get_url_hash, is_same_resource, normalize_url


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_normalize_removes_fragment(self):
        """Given: URL with fragment, When: normalize, Then: fragment removed."""
        url = "https://example.com/page#section"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_normalize_lowercases_scheme_and_host(self):
        """Given: URL with uppercase, When: normalize, Then: scheme/host lowercase."""
        url = "HTTPS://EXAMPLE.COM/Path"
        result = normalize_url(url)
        assert result == "https://example.com/Path"

    def test_normalize_removes_default_port_https(self):
        """Given: HTTPS URL with :443, When: normalize, Then: port removed."""
        url = "https://example.com:443/"
        result = normalize_url(url)
        assert result == "https://example.com"

    def test_normalize_removes_default_port_http(self):
        """Given: HTTP URL with :80, When: normalize, Then: port removed."""
        url = "http://example.com:80/page"
        result = normalize_url(url)
        assert result == "http://example.com/page"

    def test_normalize_keeps_non_default_port(self):
        """Given: URL with non-default port, When: normalize, Then: port kept."""
        url = "https://example.com:8443/page"
        result = normalize_url(url)
        assert result == "https://example.com:8443/page"

    def test_normalize_sorts_query_params(self):
        """Given: URL with unsorted params, When: normalize, Then: params sorted."""
        url = "https://example.com/search?z=3&a=1&m=2"
        result = normalize_url(url)
        assert result == "https://example.com/search?a=1&m=2&z=3"

    def test_normalize_keeps_empty_query_params(self):
        """Given: URL with empty param, When: normalize, Then: empty param kept."""
        url = "https://example.com/page?a=&b=2"
        result = normalize_url(url)
        assert result == "https://example.com/page?a=&b=2"

    def test_normalize_removes_trailing_slash(self):
        """Given: URL with trailing slash, When: normalize, Then: slash removed."""
        url = "https://example.com/page/"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_normalize_keeps_root_path(self):
        """Given: Root URL, When: normalize, Then: no trailing slash."""
        url = "https://example.com/"
        result = normalize_url(url)
        assert result == "https://example.com"

    def test_normalize_handles_relative_url_with_base(self):
        """Given: Relative URL and base, When: normalize, Then: absolute URL."""
        relative_url = "../other"
        base_url = "https://example.com/path/page"
        result = normalize_url(relative_url, base_url=base_url)
        assert result == "https://example.com/other"

    def test_normalize_handles_relative_url_same_dir(self):
        """Given: Same directory relative URL, When: normalize, Then: resolved."""
        relative_url = "sibling.html"
        base_url = "https://example.com/path/page.html"
        result = normalize_url(relative_url, base_url=base_url)
        assert result == "https://example.com/path/sibling.html"

    def test_normalize_handles_absolute_path(self):
        """Given: Absolute path with base, When: normalize, Then: resolved."""
        absolute_path = "/new/path"
        base_url = "https://example.com/old/page"
        result = normalize_url(absolute_path, base_url=base_url)
        assert result == "https://example.com/new/path"

    def test_normalize_empty_url_raises_error(self):
        """Given: Empty URL, When: normalize, Then: raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            normalize_url("")

    def test_normalize_none_url_raises_error(self):
        """Given: None URL, When: normalize, Then: raises ValueError."""
        with pytest.raises(ValueError):
            normalize_url(None)  # type: ignore

    def test_normalize_removes_duplicate_slashes(self):
        """Given: URL with duplicate slashes, When: normalize, Then: single slash."""
        url = "https://example.com//path///to////page"
        result = normalize_url(url)
        assert result == "https://example.com/path/to/page"

    def test_normalize_handles_encoded_characters(self):
        """Given: URL with encoded chars, When: normalize, Then: properly handled."""
        url = "https://example.com/path%20with%20spaces"
        result = normalize_url(url)
        # Encoded characters should be preserved
        assert "example.com" in result

    def test_normalize_complex_url(self):
        """Given: Complex URL, When: normalize, Then: all rules applied."""
        url = "HTTPS://EXAMPLE.COM:443/path//to///page/?z=3&a=1#section"
        result = normalize_url(url)
        assert result == "https://example.com/path/to/page?a=1&z=3"


class TestGetUrlHash:
    """Tests for get_url_hash function."""

    def test_get_url_hash_deterministic(self):
        """Given: Same URL different format, When: hash, Then: same hash."""
        url1 = "https://example.com/page#section"
        url2 = "HTTPS://EXAMPLE.COM/page"
        hash1 = get_url_hash(url1)
        hash2 = get_url_hash(url2)
        assert hash1 == hash2

    def test_get_url_hash_different_methods(self):
        """Given: Same URL different methods, When: hash, Then: different hash."""
        url = "https://example.com/api"
        hash_get = get_url_hash(url, method="GET")
        hash_post = get_url_hash(url, method="POST")
        assert hash_get != hash_post

    def test_get_url_hash_method_case_insensitive(self):
        """Given: Method in different case, When: hash, Then: same hash."""
        url = "https://example.com/api"
        hash1 = get_url_hash(url, method="get")
        hash2 = get_url_hash(url, method="GET")
        assert hash1 == hash2

    def test_get_url_hash_format(self):
        """Given: URL, When: hash, Then: SHA-256 hex format (64 chars)."""
        url = "https://example.com/page"
        result = get_url_hash(url)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_get_url_hash_default_method(self):
        """Given: URL without method, When: hash, Then: uses GET."""
        url = "https://example.com/page"
        hash_default = get_url_hash(url)
        hash_get = get_url_hash(url, method="GET")
        assert hash_default == hash_get


class TestIsSameResource:
    """Tests for is_same_resource function."""

    def test_is_same_resource_identical_urls(self):
        """Given: Identical URLs, When: compare, Then: True."""
        url1 = "https://example.com/page"
        url2 = "https://example.com/page"
        assert is_same_resource(url1, url2) is True

    def test_is_same_resource_different_formats(self):
        """Given: Same resource different format, When: compare, Then: True."""
        url1 = "https://example.com/page#section"
        url2 = "HTTPS://EXAMPLE.COM/page/"
        assert is_same_resource(url1, url2) is True

    def test_is_same_resource_different_query_order(self):
        """Given: Same params different order, When: compare, Then: True."""
        url1 = "https://example.com/search?a=1&b=2"
        url2 = "https://example.com/search?b=2&a=1"
        assert is_same_resource(url1, url2) is True

    def test_is_same_resource_different_urls(self):
        """Given: Different URLs, When: compare, Then: False."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert is_same_resource(url1, url2) is False

    def test_is_same_resource_different_params(self):
        """Given: Different params, When: compare, Then: False."""
        url1 = "https://example.com/search?a=1"
        url2 = "https://example.com/search?a=2"
        assert is_same_resource(url1, url2) is False

    def test_is_same_resource_with_without_query(self):
        """Given: One with query one without, When: compare, Then: False."""
        url1 = "https://example.com/page"
        url2 = "https://example.com/page?a=1"
        assert is_same_resource(url1, url2) is False
