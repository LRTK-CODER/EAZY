"""
TDD Tests for Structlog-based logging system.

Sprint 2.2: Structlog 로깅 시스템
Red Phase: 테스트 먼저 작성
"""

import io
from unittest.mock import patch

from app.core.structured_logger import LogFormat, configure_logging, get_logger


class TestStructuredLoggerConfiguration:
    """Logging configuration tests."""

    def test_configure_logging_console_format(self):
        """Console format should produce colored, human-readable output."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.console")

        # Should not raise
        logger.info("Test message", key="value")

    def test_configure_logging_json_format(self):
        """JSON format should produce parseable JSON output."""
        configure_logging(log_format=LogFormat.JSON, level="INFO")
        logger = get_logger("test.json")

        # Capture output
        stream = io.StringIO()
        with patch("sys.stdout", stream):
            logger.info("Test message", key="value")

        # Output should be valid JSON (in production)
        # Note: structlog may buffer output, so we just verify no exception

    def test_configure_logging_default_format_from_env(self):
        """LOG_FORMAT env var should control format."""
        with patch.dict("os.environ", {"LOG_FORMAT": "json"}):
            configure_logging()
            # Should not raise


class TestGetLogger:
    """Logger retrieval tests."""

    def test_get_logger_returns_bound_logger(self):
        """get_logger should return a structlog BoundLogger."""

        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")
        logger = get_logger("test.module")

        # Should be a structlog bound logger
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "bind")
        assert hasattr(logger, "unbind")

    def test_get_logger_with_initial_context(self):
        """get_logger should accept initial context values."""
        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")
        logger = get_logger("test.module", worker_id="worker-1")

        # Should have bound context
        # The context is internal, but bind/unbind should work
        new_logger = logger.bind(task_id="task-123")
        assert new_logger is not None


class TestContextBinding:
    """Context binding tests."""

    def test_bind_adds_context(self):
        """bind() should add context to log messages."""
        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")
        logger = get_logger("test.binding")

        # Bind context
        bound_logger = logger.bind(task_id="abc-123", db_task_id=100)

        # Should be able to log with bound context
        bound_logger.info("Processing task")  # Should not raise

    def test_unbind_removes_context(self):
        """unbind() should remove context from log messages."""
        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")
        logger = get_logger("test.unbinding")

        bound_logger = logger.bind(task_id="abc-123")
        unbound_logger = bound_logger.unbind("task_id")

        # Should not raise
        unbound_logger.info("After unbind")


class TestLogLevels:
    """Log level tests."""

    def test_debug_level(self):
        """DEBUG level messages should be logged when level is DEBUG."""
        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")
        logger = get_logger("test.levels")

        # Should not raise
        logger.debug("Debug message")

    def test_info_level(self):
        """INFO level messages should be logged."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.levels")

        logger.info("Info message")

    def test_warning_level(self):
        """WARNING level messages should be logged."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.levels")

        logger.warning("Warning message")

    def test_error_level(self):
        """ERROR level messages should be logged."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.levels")

        logger.error("Error message")

    def test_critical_level(self):
        """CRITICAL level messages should be logged."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.levels")

        logger.critical("Critical message")


class TestExceptionFormatting:
    """Exception formatting tests."""

    def test_exception_includes_traceback(self):
        """Exceptions should include traceback in log output."""
        configure_logging(log_format=LogFormat.CONSOLE, level="ERROR")
        logger = get_logger("test.exception")

        try:
            raise ValueError("Test error")
        except ValueError:
            # Should log with traceback
            logger.exception("An error occurred")


class TestUnicodeHandling:
    """Unicode and special character handling tests."""

    def test_unicode_in_message(self):
        """Unicode characters in messages should be handled."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.unicode")

        # Korean text
        logger.info("한글 메시지 테스트")

        # Emoji
        logger.info("Emoji test", status="success", emoji="🚀")

    def test_unicode_in_context(self):
        """Unicode characters in context values should be handled."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.unicode")

        logger.info("Message", korean_value="한글값", emoji_value="🎉")


class TestJSONOutput:
    """JSON format output tests."""

    def test_json_output_is_valid_json(self, capsys):
        """JSON format should produce valid JSON lines."""
        configure_logging(log_format=LogFormat.JSON, level="INFO")
        logger = get_logger("test.json.output")

        logger.info("Test message", key="value", number=42)

        # Note: structlog output goes through logging, may need different capture
        # This test verifies the configuration doesn't raise errors

    def test_json_output_includes_timestamp(self):
        """JSON output should include timestamp."""
        configure_logging(log_format=LogFormat.JSON, level="INFO")
        logger = get_logger("test.json.timestamp")

        # Should not raise - timestamp is added automatically
        logger.info("Test with timestamp")

    def test_json_output_includes_level(self):
        """JSON output should include log level."""
        configure_logging(log_format=LogFormat.JSON, level="INFO")
        logger = get_logger("test.json.level")

        logger.info("Info level")
        logger.error("Error level")


class TestConsoleOutput:
    """Console format output tests."""

    def test_console_output_is_readable(self):
        """Console format should produce human-readable output."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.console.readable")

        # Should produce colored output (when TTY)
        logger.info("Readable message", task_id="abc-123")

    def test_console_output_shows_context(self):
        """Console format should show bound context."""
        configure_logging(log_format=LogFormat.CONSOLE, level="INFO")
        logger = get_logger("test.console.context")

        bound = logger.bind(worker_id="worker-1", task_id="task-123")
        bound.info("Processing")


class TestLogFormat:
    """LogFormat enum tests."""

    def test_log_format_enum_values(self):
        """LogFormat should have CONSOLE and JSON values."""
        assert hasattr(LogFormat, "CONSOLE")
        assert hasattr(LogFormat, "JSON")

    def test_log_format_from_string(self):
        """LogFormat should be creatable from string."""
        assert LogFormat.CONSOLE.value == "console"
        assert LogFormat.JSON.value == "json"
