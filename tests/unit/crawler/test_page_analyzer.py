"""Unit tests for PageAnalyzer (TDD RED phase).

This test suite defines behavior for a PageAnalyzer class that analyzes
Playwright-rendered pages. Tests use AsyncMock to simulate Playwright Page
objects and elements.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eazy.crawler.page_analyzer import PageAnalyzer
from eazy.models.crawl_types import PageAnalysisResult


def _make_element(**attrs):
    """Create a mock Playwright element with given attributes.

    Args:
        **attrs: Attributes to set on the element. Use `_text` for
            text_content and `_children` for query_selector_all results.

    Returns:
        AsyncMock element with get_attribute, text_content, and
        query_selector_all methods.
    """
    el = AsyncMock()
    el.get_attribute = AsyncMock(side_effect=lambda k: attrs.get(k))
    el.text_content = AsyncMock(return_value=attrs.get("_text", ""))
    el.query_selector_all = AsyncMock(return_value=attrs.get("_children", []))
    return el


class TestPageAnalyzerExtraction:
    """Test link, form, button, and title extraction from rendered DOM."""

    @pytest.mark.asyncio
    async def test_extract_links_from_rendered_dom_returns_absolute_urls(
        self,
    ):
        """Extract links from rendered page and resolve to absolute URLs."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"

        link1 = _make_element(href="/about")
        link2 = _make_element(href="/contact")
        page.query_selector_all = AsyncMock(return_value=[link1, link2])

        # Act
        result = await analyzer.extract_links(page)

        # Assert
        assert result == [
            "https://example.com/about",
            "https://example.com/contact",
        ]

    @pytest.mark.asyncio
    async def test_extract_links_skips_javascript_href(self):
        """Skip links with javascript: protocol."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"

        link = _make_element(href="javascript:void(0)")
        page.query_selector_all = AsyncMock(return_value=[link])

        # Act
        result = await analyzer.extract_links(page)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_links_skips_anchor_only_href(self):
        """Skip fragment-only links like #section."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"

        link = _make_element(href="#section")
        page.query_selector_all = AsyncMock(return_value=[link])

        # Act
        result = await analyzer.extract_links(page)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_forms_from_rendered_page(self):
        """Extract form metadata from rendered page."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"

        input1 = _make_element(name="username", type="text")
        input2 = _make_element(name="password", type="password")

        form = _make_element(action="/login", method="POST", _children=[input1, input2])
        page.query_selector_all = AsyncMock(return_value=[form])

        # Act
        result = await analyzer.extract_forms(page)

        # Assert
        assert len(result) == 1
        assert result[0].action == "https://example.com/login"
        assert result[0].method == "POST"
        assert len(result[0].inputs) == 2
        assert result[0].has_file_upload is False

    @pytest.mark.asyncio
    async def test_extract_forms_from_spa_dynamic_content(self):
        """Detect file upload forms in SPA content."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"

        file_input = _make_element(name="avatar", type="file")
        form = _make_element(
            action="/api/submit", method="POST", _children=[file_input]
        )
        page.query_selector_all = AsyncMock(return_value=[form])

        # Act
        result = await analyzer.extract_forms(page)

        # Assert
        assert len(result) == 1
        assert result[0].has_file_upload is True

    @pytest.mark.asyncio
    async def test_extract_buttons_with_type_submit(self):
        """Extract submit button metadata."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()

        button = _make_element(type="submit", _text="Submit Form")
        page.query_selector_all = AsyncMock(return_value=[button])

        # Act
        result = await analyzer.extract_buttons(page)

        # Assert
        assert len(result) == 1
        assert result[0].text == "Submit Form"
        assert result[0].type == "submit"
        assert result[0].onclick is None

    @pytest.mark.asyncio
    async def test_extract_buttons_with_onclick(self):
        """Extract button with onclick handler."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()

        button = _make_element(type="button", onclick="handleClick()", _text="Click Me")
        page.query_selector_all = AsyncMock(return_value=[button])

        # Act
        result = await analyzer.extract_buttons(page)

        # Assert
        assert len(result) == 1
        assert result[0].onclick == "handleClick()"

    @pytest.mark.asyncio
    async def test_handle_empty_page_returns_empty_results(self):
        """Return empty results for page with no interactive elements."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.url = "https://example.com/"
        page.title = AsyncMock(return_value="")
        page.query_selector_all = AsyncMock(return_value=[])
        page.query_selector = AsyncMock(return_value=None)
        page.evaluate = AsyncMock(return_value=0)

        # Act
        result = await analyzer.analyze(page)

        # Assert
        assert isinstance(result, PageAnalysisResult)
        assert result.links == []
        assert result.forms == []
        assert result.buttons == []
        assert result.title in (None, "")

    @pytest.mark.asyncio
    async def test_extract_page_title_from_rendered_dom(self):
        """Extract page title from rendered DOM."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.title = AsyncMock(return_value="My Page Title")

        # Act
        result = await analyzer.extract_title(page)

        # Assert
        assert result == "My Page Title"


class TestPageAnalyzerSPA:
    """Test SPA detection heuristics."""

    @pytest.mark.asyncio
    async def test_detect_spa_static_html_returns_false(self):
        """Detect static HTML page as non-SPA."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        page.evaluate = AsyncMock(return_value=1)

        # Act
        result = await analyzer.detect_spa(page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_detect_spa_large_dom_diff_returns_true(self):
        """Detect SPA by large DOM difference after render."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        page.evaluate = AsyncMock(return_value=10)

        # Act
        result = await analyzer.detect_spa(page)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_detect_spa_react_root_marker_returns_true(self):
        """Detect SPA by React root marker presence."""
        # Arrange
        analyzer = PageAnalyzer(base_url="https://example.com/")
        page = AsyncMock()
        root_element = AsyncMock()
        page.query_selector = AsyncMock(return_value=root_element)
        page.evaluate = AsyncMock(return_value=1)

        # Act
        result = await analyzer.detect_spa(page)

        # Assert
        assert result is True
