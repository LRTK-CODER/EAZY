"""Pydantic data models for the crawl engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SegmentType(str, Enum):
    """URL 세그먼트 동적 타입 분류.

    URL 경로의 각 세그먼트를 분석하여 동적 파라미터의 타입을
    식별하기 위한 열거형. 우선순위: uuid → int → date → hash → slug.
    """

    UUID = "uuid"
    INT = "int"
    DATE = "date"
    HASH = "hash"
    SLUG = "slug"
    STRING = "string"


class URLPattern(BaseModel):
    """정규화된 URL 패턴.

    Attributes:
        scheme: URL 스킴 (e.g. "https").
        netloc: 호스트와 포트 (e.g. "example.com").
        pattern_path: 동적 세그먼트가 치환된 경로 패턴.
        segment_types: 경로 내 동적 세그먼트 타입 순서.
    """

    model_config = ConfigDict(frozen=True)

    scheme: str
    netloc: str
    pattern_path: str
    segment_types: tuple[SegmentType, ...]


class PatternGroup(BaseModel):
    """동일 패턴 URL 그룹.

    Attributes:
        pattern: 그룹의 URL 패턴.
        sample_urls: 대표 샘플 URL 목록.
        total_count: 이 패턴에 매칭된 전체 URL 수.
        max_samples: 보관할 최대 샘플 수.
    """

    pattern: URLPattern
    sample_urls: list[str] = Field(default_factory=list)
    total_count: int = 0
    max_samples: int = 3


class PatternNormalizationResult(BaseModel):
    """패턴 정규화 전체 결과.

    Attributes:
        groups: 패턴 그룹 목록.
        total_urls_processed: 처리된 전체 URL 수.
        total_patterns_found: 발견된 고유 패턴 수.
        total_urls_skipped: 스킵된 URL 수.
    """

    groups: list[PatternGroup] = Field(default_factory=list)
    total_urls_processed: int = 0
    total_patterns_found: int = 0
    total_urls_skipped: int = 0


class CrawlConfig(BaseModel):
    """Configuration for a crawl session.

    Attributes:
        target_url: The root URL to start crawling from.
        max_depth: Maximum link-follow depth from the root page.
        max_pages: Maximum number of pages to crawl. None means unlimited.
        respect_robots: Whether to obey robots.txt rules.
        include_subdomains: Whether to include subdomains in crawl scope.
        exclude_patterns: Glob patterns for URLs to exclude.
        user_agent: User-Agent header string sent with requests.
        request_delay: Delay in seconds between consecutive requests.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry count for failed requests.
        enable_pattern_normalization: Whether to enable URL normalization.
        max_samples_per_pattern: Max sample URLs per pattern group.
        headless: Whether to run the browser in headless mode.
        wait_until: Page load event to wait for during navigation.
        viewport_width: Browser viewport width in pixels.
        viewport_height: Browser viewport height in pixels.
        auto_detect_spa: Whether to auto-detect SPA frameworks.
    """

    model_config = ConfigDict(frozen=True)

    target_url: str
    max_depth: int = 3
    max_pages: int | None = None
    respect_robots: bool = True
    include_subdomains: bool = False
    exclude_patterns: list[str] = Field(default_factory=list)
    user_agent: str = "EAZY/0.1"
    request_delay: float = 0.0
    timeout: int = 30
    max_retries: int = 3
    enable_pattern_normalization: bool = True
    max_samples_per_pattern: int = 3
    headless: bool = True
    wait_until: Literal["networkidle", "domcontentloaded", "load", "commit"] = (
        "networkidle"
    )
    viewport_width: int = 1280
    viewport_height: int = 720
    auto_detect_spa: bool = True


class FormData(BaseModel):
    """Extracted form data from a web page.

    Attributes:
        action: Form action URL.
        method: HTTP method (GET or POST).
        inputs: List of input field metadata dicts.
        has_file_upload: Whether the form contains a file input.
    """

    action: str
    method: str = "GET"
    inputs: list[dict[str, Any]] = Field(default_factory=list)
    has_file_upload: bool = False


class EndpointInfo(BaseModel):
    """Discovered API endpoint information.

    Attributes:
        url: Endpoint URL path or full URL.
        method: HTTP method used by the endpoint.
        source: How the endpoint was discovered (e.g. "fetch", "xhr").
    """

    url: str
    method: str = "GET"
    source: str


class ButtonInfo(BaseModel):
    """Extracted button information from a web page.

    Attributes:
        text: Visible button text.
        type: Button type attribute (e.g. "submit", "button").
        onclick: Inline onclick handler code.
    """

    text: str | None = None
    type: str | None = None
    onclick: str | None = None


class PageAnalysisResult(BaseModel):
    """Result of analyzing a rendered page's DOM.

    Attributes:
        links: Absolute URLs extracted from anchor tags.
        forms: Form data extracted from form elements.
        buttons: Button information extracted from the page.
        title: Page title from the document.
        is_spa: Whether the page is detected as a Single Page Application.
    """

    links: list[str] = Field(default_factory=list)
    forms: list[FormData] = Field(default_factory=list)
    buttons: list[ButtonInfo] = Field(default_factory=list)
    title: str | None = None
    is_spa: bool = False


class PageResult(BaseModel):
    """Result of crawling a single page.

    Attributes:
        url: The crawled page URL.
        status_code: HTTP response status code.
        depth: Link depth from the root page.
        parent_url: URL of the page that linked to this one.
        title: HTML title of the page.
        links: List of discovered link URLs.
        forms: List of extracted form data.
        buttons: List of extracted button info.
        api_endpoints: List of discovered API endpoints.
        crawled_at: Timestamp when the page was crawled.
        error: Error message if the page failed to load.
    """

    url: str
    status_code: int
    depth: int
    parent_url: str | None = None
    title: str | None = None
    links: list[str] = Field(default_factory=list)
    forms: list[FormData] = Field(default_factory=list)
    buttons: list[ButtonInfo] = Field(default_factory=list)
    api_endpoints: list[EndpointInfo] = Field(default_factory=list)
    crawled_at: datetime
    error: str | None = None


class CrawlResult(BaseModel):
    """Result of an entire crawl session.

    Attributes:
        target_url: The root URL that was crawled.
        started_at: Timestamp when the crawl started.
        completed_at: Timestamp when the crawl finished.
        config: The configuration used for this crawl.
        pages: List of individual page results.
        statistics: Summary statistics of the crawl.
    """

    target_url: str
    started_at: datetime
    completed_at: datetime
    config: CrawlConfig
    pages: list[PageResult] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    pattern_groups: PatternNormalizationResult | None = None
