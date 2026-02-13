"""Unit tests for crawl data models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from eazy.models.crawl_types import (
    ButtonInfo,
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


class TestCrawlConfig:
    def test_default_values(self):
        """CrawlConfig with only target_url should have sensible defaults."""
        config = CrawlConfig(target_url="https://example.com")
        assert config.target_url == "https://example.com"
        assert config.max_depth == 3
        assert config.max_pages is None
        assert config.respect_robots is True
        assert config.include_subdomains is False
        assert config.exclude_patterns == []
        assert config.user_agent == "EAZY/0.1"
        assert config.request_delay == 0.0
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_values(self):
        """CrawlConfig should accept custom values."""
        config = CrawlConfig(
            target_url="https://test.com",
            max_depth=5,
            max_pages=100,
            respect_robots=False,
            include_subdomains=True,
            exclude_patterns=["*.pdf", "/admin/*"],
            user_agent="CustomBot/1.0",
            request_delay=1.5,
            timeout=60,
            max_retries=5,
        )
        assert config.max_depth == 5
        assert config.max_pages == 100
        assert config.respect_robots is False
        assert config.include_subdomains is True
        assert config.exclude_patterns == ["*.pdf", "/admin/*"]
        assert config.user_agent == "CustomBot/1.0"
        assert config.request_delay == 1.5
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_invalid_type_raises_error(self):
        """CrawlConfig should raise ValidationError for invalid types."""
        with pytest.raises(ValidationError):
            CrawlConfig(target_url="https://example.com", max_depth="not_a_number")


class TestFormData:
    def test_creation(self):
        """FormData should store action, method, and inputs."""
        form = FormData(
            action="/login",
            method="POST",
            inputs=[
                {"name": "username", "type": "text"},
                {"name": "password", "type": "password"},
            ],
        )
        assert form.action == "/login"
        assert form.method == "POST"
        assert len(form.inputs) == 2

    def test_default_method_is_get(self):
        """FormData method should default to GET."""
        form = FormData(action="/search")
        assert form.method == "GET"

    def test_has_file_upload_default_false(self):
        """FormData has_file_upload should default to False."""
        form = FormData(action="/upload")
        assert form.has_file_upload is False


class TestEndpointInfo:
    def test_creation(self):
        """EndpointInfo should store url, method, and source."""
        endpoint = EndpointInfo(
            url="/api/users",
            method="GET",
            source="fetch",
        )
        assert endpoint.url == "/api/users"
        assert endpoint.method == "GET"
        assert endpoint.source == "fetch"

    def test_default_method_is_get(self):
        """EndpointInfo method should default to GET."""
        endpoint = EndpointInfo(url="/api/data", source="xhr")
        assert endpoint.method == "GET"


class TestButtonInfo:
    def test_creation(self):
        """ButtonInfo should store text, type, and onclick."""
        button = ButtonInfo(
            text="Submit",
            type="submit",
            onclick="handleSubmit()",
        )
        assert button.text == "Submit"
        assert button.type == "submit"
        assert button.onclick == "handleSubmit()"

    def test_all_optional_fields(self):
        """ButtonInfo should allow all fields to be optional."""
        button = ButtonInfo()
        assert button.text is None
        assert button.type is None
        assert button.onclick is None


class TestPageResult:
    def test_creation(self):
        """PageResult should store all crawled page data."""
        now = datetime.now()
        page = PageResult(
            url="https://example.com/page",
            status_code=200,
            depth=1,
            parent_url="https://example.com",
            title="Test Page",
            links=["https://example.com/other"],
            forms=[FormData(action="/login", method="POST")],
            buttons=[ButtonInfo(text="Click")],
            api_endpoints=[EndpointInfo(url="/api/data", source="fetch")],
            crawled_at=now,
        )
        assert page.url == "https://example.com/page"
        assert page.status_code == 200
        assert page.depth == 1
        assert page.parent_url == "https://example.com"
        assert page.title == "Test Page"
        assert len(page.links) == 1
        assert len(page.forms) == 1
        assert len(page.buttons) == 1
        assert len(page.api_endpoints) == 1
        assert page.crawled_at == now

    def test_default_empty_lists(self):
        """PageResult should default to empty lists for collection fields."""
        page = PageResult(
            url="https://example.com",
            status_code=200,
            depth=0,
            crawled_at=datetime.now(),
        )
        assert page.links == []
        assert page.forms == []
        assert page.buttons == []
        assert page.api_endpoints == []

    def test_optional_fields(self):
        """PageResult optional fields should default to None."""
        page = PageResult(
            url="https://example.com",
            status_code=200,
            depth=0,
            crawled_at=datetime.now(),
        )
        assert page.parent_url is None
        assert page.title is None
        assert page.error is None


class TestCrawlResult:
    def test_creation(self):
        """CrawlResult should store full crawl session data."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
            pages=[
                PageResult(
                    url="https://example.com",
                    status_code=200,
                    depth=0,
                    crawled_at=now,
                )
            ],
            statistics={"total_pages": 1, "total_links": 0},
        )
        assert result.target_url == "https://example.com"
        assert result.started_at == now
        assert result.completed_at == now
        assert len(result.pages) == 1
        assert result.statistics["total_pages"] == 1

    def test_json_serialization(self):
        """CrawlResult should serialize to JSON via model_dump_json()."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
        )
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        assert "example.com" in json_str

    def test_json_deserialization(self):
        """CrawlResult should round-trip through JSON serialization."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
        )
        json_str = result.model_dump_json()
        restored = CrawlResult.model_validate_json(json_str)
        assert restored.target_url == result.target_url
        assert restored.config.target_url == result.config.target_url

    def test_default_empty_collections(self):
        """CrawlResult should default to empty pages and statistics."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
        )
        assert result.pages == []
        assert result.statistics == {}


class TestCrawlConfigPatternNormalization:
    """Tests for pattern normalization fields on CrawlConfig."""

    def test_crawl_config_max_samples_per_pattern_default_3(self):
        """CrawlConfig max_samples_per_pattern defaults to 3."""
        config = CrawlConfig(target_url="https://example.com")
        assert config.max_samples_per_pattern == 3

    def test_crawl_config_enable_pattern_normalization_default_true(
        self,
    ):
        """CrawlConfig enable_pattern_normalization defaults to True."""
        config = CrawlConfig(target_url="https://example.com")
        assert config.enable_pattern_normalization is True


class TestCrawlResultPatternGroups:
    """Tests for pattern_groups field on CrawlResult."""

    def test_crawl_result_has_pattern_groups_field(self):
        """CrawlResult stores a PatternNormalizationResult."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/items/<int>",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(
            pattern=pattern,
            sample_urls=["https://example.com/items/1"],
            total_count=1,
        )
        pnr = PatternNormalizationResult(
            groups=[group],
            total_urls_processed=1,
            total_patterns_found=1,
        )
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
            pattern_groups=pnr,
        )
        assert result.pattern_groups is not None
        assert len(result.pattern_groups.groups) == 1

    def test_crawl_result_pattern_groups_default_none(self):
        """CrawlResult pattern_groups defaults to None."""
        now = datetime.now()
        config = CrawlConfig(target_url="https://example.com")
        result = CrawlResult(
            target_url="https://example.com",
            started_at=now,
            completed_at=now,
            config=config,
        )
        assert result.pattern_groups is None


class TestSegmentType:
    """Tests for SegmentType enum."""

    def test_segment_type_has_all_six_values(self):
        """SegmentType should have uuid, int, date, hash, slug, string."""
        expected = {"uuid", "int", "date", "hash", "slug", "string"}
        actual = {member.value for member in SegmentType}
        assert actual == expected

    def test_segment_type_values_are_lowercase_strings(self):
        """All SegmentType values should be lowercase strings."""
        for member in SegmentType:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)


class TestURLPattern:
    """Tests for URLPattern model."""

    def test_url_pattern_creation_with_valid_data(self):
        """URLPattern should store scheme, netloc, pattern_path, segment_types."""
        pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/users/{INT}/posts/{SLUG}",
            segment_types=(SegmentType.INT, SegmentType.SLUG),
        )
        assert pattern.scheme == "https"
        assert pattern.netloc == "example.com"
        assert pattern.pattern_path == "/users/{INT}/posts/{SLUG}"
        assert pattern.segment_types == (
            SegmentType.INT,
            SegmentType.SLUG,
        )

    def test_url_pattern_frozen_immutable(self):
        """URLPattern should be immutable (frozen=True)."""
        pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/users/{INT}",
            segment_types=(SegmentType.INT,),
        )
        with pytest.raises(ValidationError):
            pattern.scheme = "http"


class TestPatternGroup:
    """Tests for PatternGroup model."""

    def test_pattern_group_creation_with_defaults(self):
        """PatternGroup should default max_samples=3 and empty lists."""
        url_pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/items/{INT}",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(pattern=url_pattern)
        assert group.pattern == url_pattern
        assert group.sample_urls == []
        assert group.total_count == 0
        assert group.max_samples == 3

    def test_pattern_group_tracks_total_count(self):
        """PatternGroup should track total_count independently."""
        url_pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/items/{INT}",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(
            pattern=url_pattern,
            sample_urls=[
                "https://example.com/items/1",
                "https://example.com/items/2",
            ],
            total_count=150,
        )
        assert group.total_count == 150
        assert len(group.sample_urls) == 2


class TestPatternNormalizationResult:
    """Tests for PatternNormalizationResult model."""

    def test_pattern_normalization_result_creation(self):
        """PatternNormalizationResult should store groups and stats."""
        url_pattern = URLPattern(
            scheme="https",
            netloc="example.com",
            pattern_path="/items/{INT}",
            segment_types=(SegmentType.INT,),
        )
        group = PatternGroup(
            pattern=url_pattern,
            sample_urls=["https://example.com/items/1"],
            total_count=10,
        )
        result = PatternNormalizationResult(
            groups=[group],
            total_urls_processed=100,
            total_patterns_found=1,
            total_urls_skipped=5,
        )
        assert len(result.groups) == 1
        assert result.total_urls_processed == 100
        assert result.total_patterns_found == 1
        assert result.total_urls_skipped == 5
