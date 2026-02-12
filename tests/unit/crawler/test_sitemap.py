"""Unit tests for sitemap module."""

from datetime import datetime

from eazy.crawler.sitemap import Sitemap

from eazy.models.crawl_types import (
    EndpointInfo,
    FormData,
    PageResult,
)


class TestSitemap:
    """Test cases for Sitemap class."""

    def _make_page(
        self,
        url: str = "https://example.com/",
        *,
        status_code: int = 200,
        depth: int = 0,
        parent_url: str | None = None,
        links: list[str] | None = None,
        forms: list[FormData] | None = None,
        api_endpoints: list[EndpointInfo] | None = None,
    ) -> PageResult:
        """Create a PageResult for testing."""
        return PageResult(
            url=url,
            status_code=status_code,
            depth=depth,
            parent_url=parent_url,
            links=links or [],
            forms=forms or [],
            api_endpoints=api_endpoints or [],
            crawled_at=datetime(2024, 1, 1, 12, 0, 0),
        )

    def test_add_page_and_get_page(self):
        """Test adding a page and retrieving it by URL."""
        # Arrange
        sitemap = Sitemap()
        page = self._make_page("https://example.com/")

        # Act
        sitemap.add_page(page)
        result = sitemap.get_page("https://example.com/")

        # Assert
        assert result is not None
        assert result.url == "https://example.com/"
        assert result.status_code == 200

    def test_get_page_not_found_returns_none(self):
        """Test get_page returns None for unknown URL."""
        # Arrange
        sitemap = Sitemap()

        # Act
        result = sitemap.get_page("https://example.com/missing")

        # Assert
        assert result is None

    def test_get_children_returns_child_pages(self):
        """Test get_children returns pages with matching parent_url."""
        # Arrange
        sitemap = Sitemap()
        parent = self._make_page("https://example.com/")
        child1 = self._make_page(
            "https://example.com/about",
            depth=1,
            parent_url="https://example.com/",
        )
        child2 = self._make_page(
            "https://example.com/contact",
            depth=1,
            parent_url="https://example.com/",
        )
        sitemap.add_page(parent)
        sitemap.add_page(child1)
        sitemap.add_page(child2)

        # Act
        children = sitemap.get_children("https://example.com/")

        # Assert
        assert len(children) == 2
        urls = {c.url for c in children}
        assert urls == {
            "https://example.com/about",
            "https://example.com/contact",
        }

    def test_get_children_no_children_returns_empty_list(self):
        """Test get_children returns empty list when no children."""
        # Arrange
        sitemap = Sitemap()
        page = self._make_page("https://example.com/")
        sitemap.add_page(page)

        # Act
        children = sitemap.get_children("https://example.com/")

        # Assert
        assert children == []

    def test_pages_property_returns_all_pages(self):
        """Test pages property returns all added pages."""
        # Arrange
        sitemap = Sitemap()
        sitemap.add_page(self._make_page("https://example.com/"))
        sitemap.add_page(
            self._make_page(
                "https://example.com/about",
                depth=1,
                parent_url="https://example.com/",
            )
        )
        sitemap.add_page(
            self._make_page(
                "https://example.com/contact",
                depth=1,
                parent_url="https://example.com/",
            )
        )

        # Act
        pages = sitemap.pages

        # Assert
        assert len(pages) == 3
        urls = {p.url for p in pages}
        assert "https://example.com/" in urls
        assert "https://example.com/about" in urls
        assert "https://example.com/contact" in urls

    def test_to_dict_contains_pages_key(self):
        """Test to_dict returns dict with pages key and URLs."""
        # Arrange
        sitemap = Sitemap()
        sitemap.add_page(self._make_page("https://example.com/"))
        sitemap.add_page(
            self._make_page(
                "https://example.com/about",
                depth=1,
                parent_url="https://example.com/",
            )
        )

        # Act
        result = sitemap.to_dict()

        # Assert
        assert "pages" in result
        assert len(result["pages"]) == 2
        urls = {p["url"] for p in result["pages"]}
        assert "https://example.com/" in urls
        assert "https://example.com/about" in urls

    def test_get_statistics_counts(self):
        """Test get_statistics returns correct counts."""
        # Arrange
        sitemap = Sitemap()
        sitemap.add_page(
            self._make_page(
                "https://example.com/",
                links=[
                    "https://example.com/a",
                    "https://example.com/b",
                    "https://example.com/c",
                ],
                forms=[FormData(action="/login", method="POST")],
                api_endpoints=[
                    EndpointInfo(
                        url="/api/users",
                        method="GET",
                        source="fetch",
                    )
                ],
            )
        )
        sitemap.add_page(
            self._make_page(
                "https://example.com/a",
                depth=1,
                parent_url="https://example.com/",
                links=[
                    "https://example.com/d",
                    "https://example.com/e",
                ],
            )
        )

        # Act
        stats = sitemap.get_statistics()

        # Assert
        assert stats["total_pages"] == 2
        assert stats["total_links"] == 5
        assert stats["total_forms"] == 1
        assert stats["total_endpoints"] == 1
