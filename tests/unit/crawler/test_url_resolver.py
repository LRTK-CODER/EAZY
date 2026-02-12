"""Unit tests for URL resolver module."""

from eazy.crawler.url_resolver import resolve_url


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
