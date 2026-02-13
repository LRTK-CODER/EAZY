"""Shared test fixtures for the EAZY test suite."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from eazy.models import CrawlConfig, CrawlResult, PageResult


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_page_result() -> PageResult:
    """Create a realistic PageResult for testing."""
    return PageResult(
        url="https://example.com/",
        status_code=200,
        depth=0,
        title="Example Domain",
        links=[
            "https://example.com/about",
            "https://example.com/contact",
        ],
        crawled_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def mock_crawl_result(mock_page_result: PageResult) -> CrawlResult:
    """Create a realistic CrawlResult for testing."""
    return CrawlResult(
        target_url="https://example.com/",
        started_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        completed_at=datetime(2025, 1, 1, 0, 0, 10, tzinfo=timezone.utc),
        config=CrawlConfig(target_url="https://example.com/"),
        pages=[mock_page_result],
        statistics={
            "total_pages": 1,
            "total_links": 2,
            "duration_seconds": 10.0,
        },
    )
