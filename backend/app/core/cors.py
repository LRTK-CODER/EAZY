"""
Sprint 2.5: CORS Configuration Module

Provides environment-based CORS configuration with production security validation.

Usage:
    from app.core.cors import get_cors_origins, validate_cors_config

    origins = get_cors_origins()
    validate_cors_config(origins, settings.ENVIRONMENT)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class CORSConfig:
    """CORS configuration container."""

    origins: List[str]
    allow_credentials: bool
    allow_methods: List[str]
    allow_headers: List[str]


def get_cors_origins(origins_str: Optional[str] = None) -> List[str]:
    """
    Parse CORS_ORIGINS from settings and return as list.

    Handles comma-separated values and strips whitespace.

    Args:
        origins_str: Optional override for CORS_ORIGINS. If None, reads from
                     environment variable or settings.

    Returns:
        List of allowed origin URLs.

    Example:
        # CORS_ORIGINS="http://localhost:3000,http://example.com"
        origins = get_cors_origins()
        # Returns: ["http://localhost:3000", "http://example.com"]
    """
    import os

    if origins_str is None:
        # Read from environment first, then fall back to settings
        origins_str = os.environ.get("CORS_ORIGINS", settings.CORS_ORIGINS)

    # Handle wildcard
    if origins_str.strip() == "*":
        return ["*"]

    # Parse comma-separated values
    origins = [origin.strip() for origin in origins_str.split(",")]

    # Filter out empty strings
    origins = [origin for origin in origins if origin]

    return origins


def validate_cors_config(
    origins: List[str], environment: str, allow_credentials: bool = True
) -> Dict[str, Any]:
    """
    Validate CORS configuration for security.

    Args:
        origins: List of allowed origins
        environment: Current environment (development, staging, production)
        allow_credentials: Whether credentials are allowed

    Returns:
        Dict with validation result:
        - valid: bool
        - warning: Optional[str]
        - error: Optional[str]

    Security Rules:
        1. Production should not use wildcard "*"
        2. Credentials cannot be used with wildcard
    """
    result: Dict[str, Any] = {
        "valid": True,
        "warning": None,
        "error": None,
    }

    is_wildcard = "*" in origins
    is_production = environment.lower() == "production"

    # Rule 1: Production + wildcard = warning/invalid
    if is_production and is_wildcard:
        result["valid"] = False
        result["warning"] = (
            "SECURITY WARNING: Using wildcard '*' for CORS origins in production "
            "is not recommended. Please specify allowed origins explicitly."
        )
        logger.warning(
            "Insecure CORS configuration",
            environment=environment,
            origins=origins,
            issue="wildcard_in_production",
        )

    # Rule 2: Credentials + wildcard = invalid (browser will reject)
    if allow_credentials and is_wildcard:
        result["valid"] = False
        result["error"] = (
            "Invalid CORS configuration: allow_credentials=True cannot be used "
            "with wildcard '*' origins. Browsers will reject this configuration."
        )
        logger.error(
            "Invalid CORS configuration",
            allow_credentials=allow_credentials,
            origins=origins,
            issue="credentials_with_wildcard",
        )

    # Log the final configuration
    if result["valid"]:
        logger.info(
            "CORS configuration validated",
            environment=environment,
            origins_count=len(origins),
            allow_credentials=allow_credentials,
        )

    return result


def get_cors_config() -> CORSConfig:
    """
    Get complete CORS configuration from settings.

    Returns:
        CORSConfig dataclass with all CORS settings.
    """
    origins = get_cors_origins()

    # Parse methods and headers
    methods = (
        ["*"]
        if settings.CORS_ALLOW_METHODS == "*"
        else [m.strip() for m in settings.CORS_ALLOW_METHODS.split(",")]
    )
    headers = (
        ["*"]
        if settings.CORS_ALLOW_HEADERS == "*"
        else [h.strip() for h in settings.CORS_ALLOW_HEADERS.split(",")]
    )

    return CORSConfig(
        origins=origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=methods,
        allow_headers=headers,
    )
