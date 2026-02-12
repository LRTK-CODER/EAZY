"""Unit tests for URL resolver module."""

from eazy.crawler.url_resolver import normalize_url, resolve_url


class TestResolveUrl:
    def test_resolve_relative_path_to_absolute_url(self):
        # Arrange
        base_url = "https://example.com/dir/page.html"
        href = "/other"

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result == "https://example.com/other"

    def test_resolve_parent_path(self):
        # Arrange
        base_url = "https://example.com/dir/sub/page.html"
        href = "../other"

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result == "https://example.com/dir/other"

    def test_resolve_protocol_relative_url(self):
        # Arrange
        base_url = "https://example.com/page"
        href = "//cdn.example.com/js/app.js"

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result == "https://cdn.example.com/js/app.js"

    def test_resolve_fragment_only_returns_none(self):
        # Arrange
        base_url = "https://example.com/page"
        href = "#section"

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result is None

    def test_resolve_empty_href_returns_none(self):
        # Arrange
        base_url = "https://example.com/page"
        href = ""

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result is None

    def test_resolve_already_absolute_url(self):
        # Arrange
        base_url = "https://example.com/page"
        href = "https://other.com/resource"

        # Act
        result = resolve_url(base_url, href)

        # Assert
        assert result == "https://other.com/resource"


class TestNormalizeUrl:
    def test_remove_fragment(self):
        # Arrange
        url = "https://example.com/page#section"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "https://example.com/page"

    def test_normalize_trailing_slash(self):
        # Arrange
        url = "https://example.com/page/"

        # Act
        result = normalize_url(url)

        # Assert
        # Trailing slash on non-root path is removed for consistency
        assert result == "https://example.com/page"

    def test_lowercase_scheme_and_host(self):
        # Arrange
        url = "HTTP://EXAMPLE.COM/Path"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "http://example.com/Path"

    def test_remove_default_port_80(self):
        # Arrange
        url = "http://example.com:80/page"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "http://example.com/page"

    def test_remove_default_port_443(self):
        # Arrange
        url = "https://example.com:443/page"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "https://example.com/page"

    def test_sort_query_parameters(self):
        # Arrange
        url = "https://example.com/search?b=2&a=1"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "https://example.com/search?a=1&b=2"

    def test_preserve_non_default_port(self):
        # Arrange
        url = "https://example.com:8080/page"

        # Act
        result = normalize_url(url)

        # Assert
        assert result == "https://example.com:8080/page"
