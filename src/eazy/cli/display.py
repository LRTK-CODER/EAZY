"""Display helpers for the EAZY CLI.

Provides a progress spinner, startup banner, and post-crawl summary
panel using Rich.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from eazy.models.crawl_types import CrawlResult


def create_progress_spinner() -> Status:
    """Create a Rich spinner for long-running operations.

    The spinner writes to stderr so it does not pollute stdout
    output captured by ``--output`` or piped to other tools.

    Returns:
        A ``rich.status.Status`` context manager.
    """
    console = Console(stderr=True)
    return console.status("[bold green]Crawling...")


def print_banner() -> None:
    """Print the EAZY startup banner to stdout."""
    console = Console()
    banner = Panel(
        "[bold cyan]EAZY[/bold cyan] - AI-powered black-box penetration testing tool",
        title="EAZY v0.1.0",
        expand=False,
    )
    console.print(banner)


def print_summary(result: CrawlResult) -> None:
    """Print a statistics summary panel after a crawl.

    Args:
        result: The completed crawl result.
    """
    stats = result.statistics
    lines = [
        f"Pages crawled: {stats.get('total_pages', 0)}",
        f"Total links:   {stats.get('total_links', 0)}",
        f"Duration:      {stats.get('duration_seconds', 0):.1f}s",
    ]
    console = Console()
    panel = Panel(
        "\n".join(lines),
        title="Crawl Summary",
        expand=False,
    )
    console.print(panel)
