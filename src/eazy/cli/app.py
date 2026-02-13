"""Typer application definition for the EAZY CLI."""

import asyncio
from pathlib import Path
from typing import Optional

import typer

from eazy.crawler.engine import CrawlerEngine
from eazy.crawler.exporter import CrawlResultExporter
from eazy.models.crawl_types import CrawlConfig

__version__ = "0.1.0"


def version_callback(value: bool) -> None:
    """Print the version string and exit.

    Args:
        value: Whether the --version flag was provided.
    """
    if value:
        typer.echo(f"eazy {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="eazy",
    help="AI-powered black-box penetration testing tool.",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """EAZY - AI-powered black-box penetration testing tool."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Target URL to crawl."),
    depth: int = typer.Option(3, "--depth", help="Maximum crawl depth."),
    max_pages: Optional[int] = typer.Option(
        None, "--max-pages", help="Maximum number of pages."
    ),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds."),
    delay: float = typer.Option(
        0.0, "--delay", help="Delay between requests in seconds."
    ),
    exclude: Optional[list[str]] = typer.Option(
        None, "--exclude", help="URL patterns to exclude."
    ),
    user_agent: str = typer.Option(
        "EAZY/0.1", "--user-agent", help="User-Agent header."
    ),
    respect_robots: bool = typer.Option(
        True,
        "--respect-robots/--no-respect-robots",
        help="Obey robots.txt rules.",
    ),
    include_subdomains: bool = typer.Option(
        False,
        "--include-subdomains",
        help="Include subdomains in scope.",
    ),
    retries: int = typer.Option(
        3, "--retries", help="Max retries for failed requests."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save results to file."
    ),
) -> None:
    """Crawl a target URL and discover its structure."""
    config = CrawlConfig(
        target_url=url,
        max_depth=depth,
        max_pages=max_pages,
        respect_robots=respect_robots,
        include_subdomains=include_subdomains,
        exclude_patterns=exclude or [],
        user_agent=user_agent,
        request_delay=delay,
        timeout=timeout,
        max_retries=retries,
    )
    engine = CrawlerEngine(config)
    result = asyncio.run(engine.crawl())

    exporter = CrawlResultExporter()
    json_output = exporter.to_json(result)

    if output:
        exporter.save_to_file(result, Path(output))
        typer.echo(f"Results saved to {output}")

    typer.echo(json_output)


@app.command()
def scan(
    url: str = typer.Argument(..., help="Target URL to scan."),
) -> None:
    """Scan a target URL for vulnerabilities."""
    typer.echo(f"Scanning {url}...")
