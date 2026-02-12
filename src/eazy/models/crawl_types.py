"""Pydantic data models for the crawl engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CrawlConfig(BaseModel):
    """Configuration for a crawl session."""

    target_url: str
    max_depth: int = 3
    max_pages: int | None = None
    respect_robots: bool = True
    include_subdomains: bool = False
    exclude_patterns: list[str] = []
    user_agent: str = "EAZY/0.1"
    request_delay: float = 0.0
    timeout: int = 30
    max_retries: int = 3


class FormData(BaseModel):
    """Extracted form data from a web page."""

    action: str
    method: str = "GET"
    inputs: list[dict[str, Any]] = []
    has_file_upload: bool = False


class EndpointInfo(BaseModel):
    """Discovered API endpoint information."""

    url: str
    method: str = "GET"
    source: str


class ButtonInfo(BaseModel):
    """Extracted button information from a web page."""

    text: str | None = None
    type: str | None = None
    onclick: str | None = None


class PageResult(BaseModel):
    """Result of crawling a single page."""

    url: str
    status_code: int
    depth: int
    parent_url: str | None = None
    title: str | None = None
    links: list[str] = []
    forms: list[FormData] = []
    buttons: list[ButtonInfo] = []
    api_endpoints: list[EndpointInfo] = []
    crawled_at: datetime
    error: str | None = None


class CrawlResult(BaseModel):
    """Result of an entire crawl session."""

    target_url: str
    started_at: datetime
    completed_at: datetime
    config: CrawlConfig
    pages: list[PageResult] = []
    statistics: dict[str, Any] = {}
