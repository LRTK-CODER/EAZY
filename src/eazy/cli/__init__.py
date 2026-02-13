"""CLI interface for the EAZY penetration testing tool."""

from eazy.cli.app import app


def main() -> None:
    """Entry point for the eazy CLI."""
    app()


__all__ = ["app", "main"]
