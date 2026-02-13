"""Unit tests for CLI output formatters."""

from __future__ import annotations

import json

import pytest

from eazy.cli.formatters import (
    JsonFormatter,
    TableFormatter,
    TextFormatter,
    format_result,
)
from eazy.models import CrawlResult


class TestJsonFormatter:
    """Tests for JSON output formatter."""

    def test_format_returns_valid_json_string(
        self, mock_crawl_result: CrawlResult
    ) -> None:
        formatter = JsonFormatter()
        output = formatter.format(mock_crawl_result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_format_includes_pages(self, mock_crawl_result: CrawlResult) -> None:
        formatter = JsonFormatter()
        output = formatter.format(mock_crawl_result)
        parsed = json.loads(output)
        assert "pages" in parsed
        assert len(parsed["pages"]) == 1

    def test_format_includes_statistics(self, mock_crawl_result: CrawlResult) -> None:
        formatter = JsonFormatter()
        output = formatter.format(mock_crawl_result)
        parsed = json.loads(output)
        assert "statistics" in parsed
        assert parsed["statistics"]["total_pages"] == 1

    def test_format_includes_config(self, mock_crawl_result: CrawlResult) -> None:
        formatter = JsonFormatter()
        output = formatter.format(mock_crawl_result)
        parsed = json.loads(output)
        assert "config" in parsed
        assert parsed["config"]["target_url"] == "https://example.com/"


class TestTextFormatter:
    """Tests for plain text output formatter."""

    def test_format_returns_string(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_includes_statistics_summary(
        self, mock_crawl_result: CrawlResult
    ) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert "1" in output  # total_pages
        assert "2" in output  # total_links

    def test_format_includes_page_urls(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert "https://example.com/" in output

    def test_format_includes_status_codes(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert "200" in output

    def test_format_shows_forms_count(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert "forms=0" in output

    def test_format_shows_endpoints_count(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TextFormatter()
        output = formatter.format(mock_crawl_result)
        assert "endpoints=0" in output


class TestTableFormatter:
    """Tests for Rich table output formatter."""

    def test_format_returns_string(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TableFormatter()
        output = formatter.format(mock_crawl_result)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_includes_url_column(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TableFormatter()
        output = formatter.format(mock_crawl_result)
        assert "https://example.com/" in output

    def test_format_includes_status_column(
        self, mock_crawl_result: CrawlResult
    ) -> None:
        formatter = TableFormatter()
        output = formatter.format(mock_crawl_result)
        assert "200" in output

    def test_format_includes_depth_column(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TableFormatter()
        output = formatter.format(mock_crawl_result)
        # Depth 0 should appear in the table
        assert "0" in output

    def test_format_includes_summary_row(self, mock_crawl_result: CrawlResult) -> None:
        formatter = TableFormatter()
        output = formatter.format(mock_crawl_result)
        # Summary row should show total pages count
        assert "Total" in output or "total" in output


class TestFormatResult:
    """Tests for the format_result dispatcher function."""

    def test_dispatch_json(self, mock_crawl_result: CrawlResult) -> None:
        output = format_result(mock_crawl_result, "json")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_dispatch_text(self, mock_crawl_result: CrawlResult) -> None:
        output = format_result(mock_crawl_result, "text")
        assert "https://example.com/" in output
        # Should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

    def test_dispatch_table(self, mock_crawl_result: CrawlResult) -> None:
        output = format_result(mock_crawl_result, "table")
        assert "https://example.com/" in output

    def test_invalid_format_raises_error(self, mock_crawl_result: CrawlResult) -> None:
        with pytest.raises(ValueError, match="Unknown format"):
            format_result(mock_crawl_result, "xml")
