"""Output formatters for crawl results.

Provides JSON, plain text, and Rich table formatters with a
dispatcher function for the CLI --format option.
"""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.table import Table

from eazy.crawler.exporter import CrawlResultExporter
from eazy.models.crawl_types import CrawlResult, PageResult


def _page_stats(page: PageResult) -> dict[str, int]:
    """Extract display-relevant counts from a single page.

    Args:
        page: The page result to summarise.

    Returns:
        Dict with links, forms, and endpoints counts.
    """
    return {
        "links": len(page.links),
        "forms": len(page.forms),
        "endpoints": len(page.api_endpoints),
    }


class JsonFormatter:
    """Format a CrawlResult as a JSON string.

    Delegates to ``CrawlResultExporter.to_json`` so the output is
    identical to the ``--output`` file format.
    """

    def format(self, result: CrawlResult) -> str:
        """Serialize the crawl result to pretty-printed JSON.

        Args:
            result: Crawl result to format.

        Returns:
            JSON string with indent=2.
        """
        return CrawlResultExporter().to_json(result)


class TextFormatter:
    """Format a CrawlResult as human-readable plain text."""

    def format(self, result: CrawlResult) -> str:
        """Render the crawl result as plain text.

        Args:
            result: Crawl result to format.

        Returns:
            Multi-line plain text summary.
        """
        stats = result.statistics
        lines: list[str] = [
            f"Crawl Results: {result.target_url}",
            "",
            "Statistics:",
            f"  Pages crawled: {stats.get('total_pages', 0)}",
            f"  Total links:   {stats.get('total_links', 0)}",
            f"  Duration:      {stats.get('duration_seconds', 0):.1f}s",
            "",
            "Pages:",
        ]
        for page in result.pages:
            ps = _page_stats(page)
            lines.append(
                f"  {page.url} [{page.status_code}]"
                f" depth={page.depth}"
                f" links={ps['links']}"
                f" forms={ps['forms']}"
                f" endpoints={ps['endpoints']}"
            )
        return "\n".join(lines) + "\n"


class TableFormatter:
    """Format a CrawlResult as a Rich table captured to string."""

    def format(self, result: CrawlResult) -> str:
        """Render the crawl result as a Rich table.

        Args:
            result: Crawl result to format.

        Returns:
            String containing the rendered table with ANSI codes
            stripped.
        """
        table = Table(
            title=f"Crawl Results: {result.target_url}",
            show_lines=False,
        )
        table.add_column("URL", style="cyan", no_wrap=True)
        table.add_column("Status", justify="right")
        table.add_column("Depth", justify="right")
        table.add_column("Links", justify="right")
        table.add_column("Forms", justify="right")
        table.add_column("Endpoints", justify="right")

        for page in result.pages:
            ps = _page_stats(page)
            table.add_row(
                page.url,
                str(page.status_code),
                str(page.depth),
                str(ps["links"]),
                str(ps["forms"]),
                str(ps["endpoints"]),
            )

        stats = result.statistics
        table.add_section()
        table.add_row(
            "Total",
            f"{stats.get('total_pages', 0)} pages",
            "",
            str(stats.get("total_links", 0)),
            "",
            "",
            style="bold",
        )

        buf = StringIO()
        console = Console(file=buf, force_terminal=False, width=120)
        console.print(table)
        return buf.getvalue()


def format_result(result: CrawlResult, format_type: str) -> str:
    """Dispatch to the appropriate formatter.

    Args:
        result: Crawl result to format.
        format_type: One of ``"json"``, ``"text"``, or ``"table"``.

    Returns:
        Formatted string.

    Raises:
        ValueError: If *format_type* is not recognised.
    """
    formatters: dict[str, JsonFormatter | TextFormatter | TableFormatter] = {
        "json": JsonFormatter(),
        "text": TextFormatter(),
        "table": TableFormatter(),
    }
    formatter = formatters.get(format_type)
    if formatter is None:
        raise ValueError(
            f"Unknown format '{format_type}'. Choose from: {', '.join(formatters)}"
        )
    return formatter.format(result)
