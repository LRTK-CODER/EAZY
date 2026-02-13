"""Unit tests for CLI app structure and entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from eazy.cli.app import app

runner = CliRunner()


class TestAppHelp:
    """Tests for --help output."""

    def test_help_returns_exit_code_zero(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_shows_usage(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "Usage" in result.output

    def test_no_args_shows_help_text(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage" in result.output or "crawl" in result.output


class TestAppVersion:
    """Tests for --version flag."""

    def test_version_returns_exit_code_zero(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_shows_version_string(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert "0.1.0" in result.output


class TestSubcommandRegistration:
    """Tests for subcommand availability."""

    def test_crawl_subcommand_registered(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "crawl" in result.output

    def test_scan_subcommand_registered(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "scan" in result.output

    def test_crawl_help_returns_exit_code_zero(self) -> None:
        result = runner.invoke(app, ["crawl", "--help"])
        assert result.exit_code == 0

    def test_scan_help_returns_exit_code_zero(self) -> None:
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
