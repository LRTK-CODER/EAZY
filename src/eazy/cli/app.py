"""Typer application definition for the EAZY CLI."""

from typing import Optional

import typer

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
) -> None:
    """Crawl a target URL and discover its structure."""
    typer.echo(f"Crawling {url}...")


@app.command()
def scan(
    url: str = typer.Argument(..., help="Target URL to scan."),
) -> None:
    """Scan a target URL for vulnerabilities."""
    typer.echo(f"Scanning {url}...")
