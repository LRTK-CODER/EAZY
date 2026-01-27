"""
Tests for Task model crawl_url field validation.

This module tests the crawl_url field validator that ensures:
- None is allowed (root tasks)
- Empty strings are rejected
- Only absolute URLs (http/https) are allowed
- Dangerous schemes (javascript, data, file) are rejected
"""

import pytest
from pydantic import ValidationError

from app.models.task import TaskBase, TaskType


class TestCrawlUrlValidation:
    """Test crawl_url field validation in TaskBase model."""

    def test_crawl_url_none_allowed(self):
        """None is allowed for root tasks that use target.url."""
        task = TaskBase(
            project_id=1,
            crawl_url=None,
        )
        assert task.crawl_url is None

    def test_crawl_url_valid_https(self):
        """Valid HTTPS URL should be accepted."""
        task = TaskBase(
            project_id=1,
            crawl_url="https://example.com/page",
        )
        assert task.crawl_url == "https://example.com/page"

    def test_crawl_url_valid_http(self):
        """Valid HTTP URL should be accepted."""
        task = TaskBase(
            project_id=1,
            crawl_url="http://example.com/page",
        )
        assert task.crawl_url == "http://example.com/page"

    def test_crawl_url_with_query_params(self):
        """URL with query parameters should be accepted."""
        url = "https://example.com/search?q=test&page=1"
        task = TaskBase(
            project_id=1,
            crawl_url=url,
        )
        assert task.crawl_url == url

    def test_crawl_url_with_fragment(self):
        """URL with fragment should be accepted."""
        url = "https://example.com/page#section"
        task = TaskBase(
            project_id=1,
            crawl_url=url,
        )
        assert task.crawl_url == url

    def test_crawl_url_with_port(self):
        """URL with port should be accepted."""
        url = "https://example.com:8080/api"
        task = TaskBase(
            project_id=1,
            crawl_url=url,
        )
        assert task.crawl_url == url

    def test_crawl_url_strips_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        task = TaskBase(
            project_id=1,
            crawl_url="  https://example.com  ",
        )
        assert task.crawl_url == "https://example.com"

    def test_crawl_url_empty_string_rejected(self):
        """Empty string should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="",
            )
        assert "crawl_url cannot be empty" in str(exc_info.value)

    def test_crawl_url_whitespace_only_rejected(self):
        """Whitespace-only string should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="   ",
            )
        assert "crawl_url cannot be empty" in str(exc_info.value)

    def test_crawl_url_relative_url_rejected(self):
        """Relative URL should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="/relative/path",
            )
        assert "must be absolute URL" in str(exc_info.value)

    def test_crawl_url_no_scheme_rejected(self):
        """URL without scheme should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="example.com/path",
            )
        assert "must be absolute URL" in str(exc_info.value)

    def test_crawl_url_javascript_scheme_rejected(self):
        """JavaScript scheme should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="javascript:alert('xss')",
            )
        assert "dangerous scheme" in str(exc_info.value)

    def test_crawl_url_data_scheme_rejected(self):
        """Data scheme should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="data:text/html,<h1>test</h1>",
            )
        assert "dangerous scheme" in str(exc_info.value)

    def test_crawl_url_file_scheme_rejected(self):
        """File scheme should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="file:///etc/passwd",
            )
        assert "dangerous scheme" in str(exc_info.value)

    def test_crawl_url_vbscript_scheme_rejected(self):
        """VBScript scheme should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="vbscript:msgbox('test')",
            )
        assert "dangerous scheme" in str(exc_info.value)

    def test_crawl_url_case_insensitive_scheme_check(self):
        """Scheme check should be case-insensitive."""
        # Valid HTTPS with different case
        task = TaskBase(
            project_id=1,
            crawl_url="HTTPS://example.com",
        )
        assert task.crawl_url == "HTTPS://example.com"

        # Dangerous scheme with different case
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url="JAVASCRIPT:void(0)",
            )
        assert "dangerous scheme" in str(exc_info.value)

    def test_crawl_url_max_length_enforced(self):
        """URL exceeding max_length should be rejected."""
        # Create URL that exceeds 2048 characters
        long_path = "a" * 2040
        long_url = f"https://example.com/{long_path}"

        with pytest.raises(ValidationError) as exc_info:
            TaskBase(
                project_id=1,
                crawl_url=long_url,
            )
        # Pydantic will raise error about max_length
        assert "2048" in str(exc_info.value) or "max" in str(exc_info.value).lower()

    def test_crawl_url_unicode_domain_allowed(self):
        """Unicode (IDN) domains should be allowed."""
        task = TaskBase(
            project_id=1,
            crawl_url="https://例え.jp/path",
        )
        assert "例え.jp" in task.crawl_url

    def test_crawl_url_ip_address_allowed(self):
        """IP address URLs should be allowed (SSRF check is separate)."""
        task = TaskBase(
            project_id=1,
            crawl_url="http://192.168.1.1/admin",
        )
        assert task.crawl_url == "http://192.168.1.1/admin"


class TestTaskBaseWithAllFields:
    """Test TaskBase with all fields including crawl_url."""

    def test_task_with_all_recursive_fields(self):
        """Test task creation with all recursive crawling fields."""
        task = TaskBase(
            project_id=1,
            target_id=10,
            type=TaskType.CRAWL,
            depth=2,
            max_depth=5,
            parent_task_id=100,
            crawl_url="https://example.com/discovered-page",
        )
        assert task.project_id == 1
        assert task.target_id == 10
        assert task.depth == 2
        assert task.max_depth == 5
        assert task.parent_task_id == 100
        assert task.crawl_url == "https://example.com/discovered-page"

    def test_root_task_without_crawl_url(self):
        """Root task (no parent) should work without crawl_url."""
        task = TaskBase(
            project_id=1,
            target_id=10,
            type=TaskType.CRAWL,
            depth=0,
            max_depth=3,
            parent_task_id=None,
            crawl_url=None,
        )
        assert task.parent_task_id is None
        assert task.crawl_url is None
        assert task.depth == 0
