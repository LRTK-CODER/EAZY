"""
Structlog-based logging system for EAZY backend.

Sprint 2.2: Structlog 로깅 시스템

Provides structured logging with:
- Console format for development (colored, human-readable)
- JSON format for production (machine-parseable)
- Context binding for request/task tracking
- Automatic exception formatting

Usage:
    from app.core.structured_logger import configure_logging, get_logger

    # At application startup
    configure_logging()

    # Get a logger
    logger = get_logger(__name__)

    # Log with context
    logger.info("Processing task", task_id="abc-123", db_task_id=100)

    # Bind context for multiple log calls
    log = logger.bind(worker_id="worker-1")
    log.info("Started processing")
    log.info("Finished processing")
"""

import logging
import os
import sys
from enum import Enum
from typing import Any, Optional

import structlog
from structlog.typing import Processor


class LogFormat(str, Enum):
    """Supported log output formats."""

    CONSOLE = "console"
    JSON = "json"


# Global flag to track if logging is configured
_logging_configured = False


def configure_logging(
    log_format: Optional[LogFormat] = None,
    level: str = "INFO",
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_format: Output format (console or json). If None, reads from LOG_FORMAT env var.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        # Development (colored console output)
        configure_logging(log_format=LogFormat.CONSOLE, level="DEBUG")

        # Production (JSON output)
        configure_logging(log_format=LogFormat.JSON, level="INFO")

        # Auto-detect from environment
        configure_logging()  # Uses LOG_FORMAT env var
    """
    global _logging_configured

    # Determine format
    if log_format is None:
        format_str = os.environ.get("LOG_FORMAT", "console").lower()
        log_format = LogFormat.JSON if format_str == "json" else LogFormat.CONSOLE

    # Set up log level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Common processors for all formats
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == LogFormat.JSON:
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        # Use StreamHandler for JSON output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        # Console format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=sys.stderr.isatty(),
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
        # Use StreamHandler for console output
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))

    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,  # Don't cache for testing
    )

    _logging_configured = True


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger for the given module name.

    Args:
        name: Logger name (usually __name__)
        **initial_context: Initial context values to bind

    Returns:
        A structlog BoundLogger instance

    Example:
        # Basic usage
        logger = get_logger(__name__)
        logger.info("Hello world")

        # With initial context
        logger = get_logger(__name__, worker_id="worker-1")
        logger.info("Processing")  # Includes worker_id in output
    """
    # Ensure logging is configured
    if not _logging_configured:
        configure_logging()

    logger = structlog.get_logger(name)

    if initial_context:
        logger = logger.bind(**initial_context)

    return logger


def reset_logging_configuration() -> None:
    """
    Reset logging configuration. Useful for testing.
    """
    global _logging_configured
    _logging_configured = False
    structlog.reset_defaults()
