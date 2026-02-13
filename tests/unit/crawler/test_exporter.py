"""Unit tests for crawl result exporter module."""

import json
from datetime import datetime
from pathlib import Path

from eazy.crawler.exporter import CrawlResultExporter
from eazy.models.crawl_types import (
    CrawlConfig,
    CrawlResult,
    EndpointInfo,
    FormData,
    PageResult,
    PatternGroup,
    PatternNormalizationResult,
    SegmentType,
    URLPattern,
)


class TestCrawlResultExporter:
    """Test cases for CrawlResultExporter class."""

    def _make_crawl_result(self) -> CrawlResult:
        """Create a sample CrawlResult for testing."""
        config = CrawlConfig(target_url="https://example.com")
        page = PageResult(
            url="https://example.com/",
            status_code=200,
            depth=0,
            title="Example",
            links=["https://example.com/about", "https://example.com/contact"],
            forms=[FormData(action="/login", method="POST")],
            api_endpoints=[
                EndpointInfo(url="/api/users", method="GET", source="fetch")
            ],
            crawled_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        return CrawlResult(
            target_url="https://example.com",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 0),
            config=config,
            pages=[page],
        )

    def test_to_json_returns_valid_json(self):
        """Test to_json returns valid parseable JSON string."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()

        # Act
        json_str = exporter.to_json(result)

        # Assert
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_to_json_contains_urls(self):
        """Test to_json output contains URLs from pages."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()

        # Act
        json_str = exporter.to_json(result)

        # Assert
        parsed = json.loads(json_str)
        assert "pages" in parsed
        assert len(parsed["pages"]) == 1
        page = parsed["pages"][0]
        assert page["url"] == "https://example.com/"
        assert "https://example.com/about" in page["links"]
        assert "https://example.com/contact" in page["links"]

    def test_to_json_contains_forms(self):
        """Test to_json output contains forms from pages."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()

        # Act
        json_str = exporter.to_json(result)

        # Assert
        parsed = json.loads(json_str)
        page = parsed["pages"][0]
        assert "forms" in page
        assert len(page["forms"]) == 1
        form = page["forms"][0]
        assert form["action"] == "/login"
        assert form["method"] == "POST"

    def test_to_json_contains_endpoints(self):
        """Test to_json output contains API endpoints from pages."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()

        # Act
        json_str = exporter.to_json(result)

        # Assert
        parsed = json.loads(json_str)
        page = parsed["pages"][0]
        assert "api_endpoints" in page
        assert len(page["api_endpoints"]) == 1
        endpoint = page["api_endpoints"][0]
        assert endpoint["url"] == "/api/users"
        assert endpoint["method"] == "GET"
        assert endpoint["source"] == "fetch"

    def test_to_json_contains_metadata(self):
        """Test to_json output contains top-level metadata fields."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()

        # Act
        json_str = exporter.to_json(result)

        # Assert
        parsed = json.loads(json_str)
        assert "target_url" in parsed
        assert parsed["target_url"] == "https://example.com"
        assert "started_at" in parsed
        assert "completed_at" in parsed
        assert "config" in parsed
        assert parsed["config"]["target_url"] == "https://example.com"

    def test_save_to_file_creates_json_file(self, tmp_path: Path):
        """Test save_to_file creates a readable JSON file."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()
        output_path = tmp_path / "output.json"

        # Act
        exporter.save_to_file(result, output_path)

        # Assert
        assert output_path.exists()
        assert output_path.is_file()
        content = output_path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_save_to_file_content_matches_to_json(self, tmp_path: Path):
        """Test save_to_file writes same content as to_json returns."""
        # Arrange
        exporter = CrawlResultExporter()
        result = self._make_crawl_result()
        output_path = tmp_path / "output.json"

        # Act
        json_str = exporter.to_json(result)
        exporter.save_to_file(result, output_path)

        # Assert
        file_content = output_path.read_text(encoding="utf-8")
        assert file_content == json_str

    def test_export_json_includes_pattern_groups(self):
        """JSON export includes pattern_groups when present."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com")
        pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/posts/<int>",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(
            pattern=pattern,
            sample_urls=["https://example.com/posts/1"],
            total_count=5,
        )
        pnr = PatternNormalizationResult(
            groups=[group],
            total_urls_processed=10,
            total_patterns_found=1,
            total_urls_skipped=4,
        )
        result = CrawlResult(
            target_url="https://example.com",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 0),
            config=config,
            pattern_groups=pnr,
        )
        exporter = CrawlResultExporter()

        # Act
        json_str = exporter.to_json(result)
        parsed = json.loads(json_str)

        # Assert
        assert "pattern_groups" in parsed
        assert parsed["pattern_groups"] is not None

    def test_export_json_pattern_group_has_statistics(self):
        """JSON export pattern_groups contains statistics and samples."""
        # Arrange
        config = CrawlConfig(target_url="https://example.com")
        pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/posts/<int>",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(
            pattern=pattern,
            sample_urls=[
                "https://example.com/posts/1",
                "https://example.com/posts/2",
            ],
            total_count=10,
        )
        pnr = PatternNormalizationResult(
            groups=[group],
            total_urls_processed=15,
            total_patterns_found=1,
            total_urls_skipped=8,
        )
        result = CrawlResult(
            target_url="https://example.com",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 0),
            config=config,
            pattern_groups=pnr,
        )
        exporter = CrawlResultExporter()

        # Act
        json_str = exporter.to_json(result)
        parsed = json.loads(json_str)

        # Assert
        pg = parsed["pattern_groups"]
        assert pg["total_urls_processed"] == 15
        assert isinstance(pg["groups"][0]["sample_urls"], list)
        assert len(pg["groups"][0]["sample_urls"]) == 2
