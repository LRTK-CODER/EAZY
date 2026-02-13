"""Unit tests for CLI display helpers."""

from __future__ import annotations

from eazy.cli.display import (
    create_progress_spinner,
    print_banner,
    print_summary,
)
from eazy.models import CrawlResult


class TestProgressSpinner:
    """Tests for the progress spinner context manager."""

    def test_create_progress_spinner_returns_context_manager(
        self,
    ) -> None:
        spinner = create_progress_spinner()
        assert hasattr(spinner, "__enter__")
        assert hasattr(spinner, "__exit__")


class TestBanner:
    """Tests for the banner display."""

    def test_print_banner_runs_without_exception(self, capsys) -> None:
        print_banner()
        # Should not raise; output goes to stdout
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestSummary:
    """Tests for the summary display."""

    def test_print_summary_includes_statistics(
        self, mock_crawl_result: CrawlResult, capsys
    ) -> None:
        print_summary(mock_crawl_result)
        captured = capsys.readouterr()
        # Should contain statistics values
        assert "1" in captured.out  # total_pages
        assert "2" in captured.out  # total_links
