"""Unit tests for HTML regex parser."""

import pytest

from eazy.crawler.regex_parser import extract_links


class TestExtractLinks:
    def test_extract_links_from_basic_anchor_tag(self):
        # Arrange
        html = '<a href="/page">Link</a>'

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/page"]

    def test_extract_links_from_multiple_anchors(self):
        # Arrange
        html = """
            <a href="/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="/page3">Link 3</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/page1", "https://example.com/page2", "/page3"]

    def test_extract_links_from_empty_html_returns_empty_list(self):
        # Arrange
        html = ""

        # Act
        result = extract_links(html)

        # Assert
        assert result == []

    def test_extract_links_ignores_anchor_without_href(self):
        # Arrange
        html = '<a name="top">No Link</a>'

        # Act
        result = extract_links(html)

        # Assert
        assert result == []

    def test_extract_links_handles_both_quote_styles(self):
        # Arrange
        html = """
            <a href="/double-quotes">Link 1</a>
            <a href='/single-quotes'>Link 2</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/double-quotes", "/single-quotes"]

    def test_extract_links_ignores_javascript_mailto_tel_protocols(self):
        # Arrange
        html = """
            <a href="javascript:void(0)">JS Link</a>
            <a href="mailto:a@b.com">Email</a>
            <a href="tel:123">Phone</a>
            <a href="/valid">Valid Link</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/valid"]
