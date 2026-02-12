"""Sitemap module for managing crawled page structure.

Provides a tree-like structure to store and query crawled pages
by URL, parent-child relationships, and aggregate statistics.
"""

from __future__ import annotations

from eazy.models.crawl_types import PageResult


class Sitemap:
    """In-memory sitemap storing crawled pages keyed by URL.

    Attributes:
        _pages: Internal dict mapping URL to PageResult.
    """

    def __init__(self) -> None:
        self._pages: dict[str, PageResult] = {}

    def add_page(self, page: PageResult) -> None:
        """Add a crawled page to the sitemap.

        Args:
            page: The page result to store.
        """
        self._pages[page.url] = page

    def get_page(self, url: str) -> PageResult | None:
        """Retrieve a page by its URL.

        Args:
            url: The URL to look up.

        Returns:
            The PageResult if found, None otherwise.
        """
        return self._pages.get(url)

    def get_children(self, url: str) -> list[PageResult]:
        """Get all pages whose parent_url matches the given URL.

        Args:
            url: The parent URL to search for.

        Returns:
            List of child PageResult objects.
        """
        return [p for p in self._pages.values() if p.parent_url == url]

    @property
    def pages(self) -> list[PageResult]:
        """Return all stored pages.

        Returns:
            List of all PageResult objects.
        """
        return list(self._pages.values())

    def to_dict(self) -> dict:
        """Convert sitemap to a dictionary.

        Returns:
            Dict with a 'pages' key containing serialized pages.
        """
        return {
            "pages": [p.model_dump(mode="json") for p in self._pages.values()],
        }

    def get_statistics(self) -> dict:
        """Compute aggregate statistics across all pages.

        Returns:
            Dict with total_pages, total_links, total_forms,
            and total_endpoints counts.
        """
        total_links = sum(len(p.links) for p in self._pages.values())
        total_forms = sum(len(p.forms) for p in self._pages.values())
        total_endpoints = sum(len(p.api_endpoints) for p in self._pages.values())
        return {
            "total_pages": len(self._pages),
            "total_links": total_links,
            "total_forms": total_forms,
            "total_endpoints": total_endpoints,
        }
