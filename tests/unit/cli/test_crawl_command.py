"""Unit tests for the crawl CLI command."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from eazy.cli.app import app

runner = CliRunner()


def _make_mock_engine(mock_crawl_result):
    """Create a mock CrawlerEngine that returns mock_crawl_result."""
    mock_engine = AsyncMock()
    mock_engine.crawl.return_value = mock_crawl_result
    mock_cls = AsyncMock(return_value=mock_engine)
    return mock_cls


class TestCrawlDefaultExecution:
    """Tests for crawl command basic execution."""

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_calls_engine_with_default_config(
        self, mock_engine_cls, mock_crawl_result
    ):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["crawl", "http://example.com"])

        assert result.exit_code == 0
        mock_engine_cls.assert_called_once()
        config = mock_engine_cls.call_args[0][0]
        assert config.target_url == "http://example.com"
        assert config.max_depth == 3
        assert config.respect_robots is True
        assert config.include_subdomains is False
        mock_engine.crawl.assert_called_once()

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_outputs_json_to_stdout(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["crawl", "http://example.com"])

        assert result.exit_code == 0
        assert "example.com" in result.output


class TestCrawlOptions:
    """Tests for crawl command CLI options."""

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_depth_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(app, ["crawl", "http://example.com", "--depth", "5"])

        config = mock_engine_cls.call_args[0][0]
        assert config.max_depth == 5

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_max_pages_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(app, ["crawl", "http://example.com", "--max-pages", "100"])

        config = mock_engine_cls.call_args[0][0]
        assert config.max_pages == 100

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_timeout_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(app, ["crawl", "http://example.com", "--timeout", "60"])

        config = mock_engine_cls.call_args[0][0]
        assert config.timeout == 60

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_delay_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(app, ["crawl", "http://example.com", "--delay", "0.5"])

        config = mock_engine_cls.call_args[0][0]
        assert config.request_delay == 0.5

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_exclude_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(app, ["crawl", "http://example.com", "--exclude", "*.pdf"])

        config = mock_engine_cls.call_args[0][0]
        assert "*.pdf" in config.exclude_patterns

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_multiple_exclude_options(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(
            app,
            [
                "crawl",
                "http://example.com",
                "--exclude",
                "*.pdf",
                "--exclude",
                "*.jpg",
            ],
        )

        config = mock_engine_cls.call_args[0][0]
        assert "*.pdf" in config.exclude_patterns
        assert "*.jpg" in config.exclude_patterns

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_user_agent_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(
            app,
            ["crawl", "http://example.com", "--user-agent", "MyBot/1.0"],
        )

        config = mock_engine_cls.call_args[0][0]
        assert config.user_agent == "MyBot/1.0"

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_no_respect_robots_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(
            app,
            ["crawl", "http://example.com", "--no-respect-robots"],
        )

        config = mock_engine_cls.call_args[0][0]
        assert config.respect_robots is False

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_include_subdomains_option(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        runner.invoke(
            app,
            ["crawl", "http://example.com", "--include-subdomains"],
        )

        config = mock_engine_cls.call_args[0][0]
        assert config.include_subdomains is True


class TestCrawlOutput:
    """Tests for crawl command output options."""

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_output_saves_to_file(
        self, mock_engine_cls, mock_crawl_result, tmp_path
    ):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        outfile = tmp_path / "result.json"
        runner.invoke(
            app,
            [
                "crawl",
                "http://example.com",
                "--output",
                str(outfile),
            ],
        )

        assert outfile.exists()
        content = outfile.read_text()
        assert "example.com" in content


class TestCrawlFormatOption:
    """Tests for crawl command --format option."""

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_format_json_outputs_valid_json(
        self, mock_engine_cls, mock_crawl_result
    ):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["crawl", "http://example.com", "--format", "json"])

        assert result.exit_code == 0
        import json

        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)
        assert "pages" in parsed

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_format_text_outputs_text_summary(
        self, mock_engine_cls, mock_crawl_result
    ):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["crawl", "http://example.com", "--format", "text"])

        assert result.exit_code == 0
        assert "example.com" in result.output

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_format_table_outputs_table(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(
            app, ["crawl", "http://example.com", "--format", "table"]
        )

        assert result.exit_code == 0
        assert "example.com" in result.output

    @patch("eazy.cli.app.CrawlerEngine")
    def test_crawl_default_format_is_table(self, mock_engine_cls, mock_crawl_result):
        mock_engine = AsyncMock()
        mock_engine.crawl.return_value = mock_crawl_result
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["crawl", "http://example.com"])

        assert result.exit_code == 0
        # Default is table format, which contains "Total" summary
        assert "Total" in result.output or "total" in result.output


class TestCrawlErrorHandling:
    """Tests for crawl command error handling."""

    def test_crawl_missing_url_shows_error(self):
        result = runner.invoke(app, ["crawl"])

        assert result.exit_code != 0
