"""Unified API error response schema.

Inspired by RFC 7807 Problem Details for HTTP APIs.
"""

from typing import Any, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Unified error response schema for all API errors.

    Attributes:
        error: Machine-readable error code (e.g., "TARGET_NOT_FOUND")
        message: Human-readable description
        status_code: HTTP status code (redundant but useful for clients)
        detail: Optional additional context
    """

    error: str
    message: str
    status_code: int
    detail: Optional[dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "TARGET_NOT_FOUND",
                    "message": "Target not found: 123",
                    "status_code": 404,
                    "detail": {"target_id": 123},
                },
                {
                    "error": "DUPLICATE_SCAN",
                    "message": "Scan already in progress for target: 456",
                    "status_code": 409,
                    "detail": {"target_id": 456},
                },
                {
                    "error": "UNSAFE_URL",
                    "message": "Unsafe URL detected: http://127.0.0.1/admin",
                    "status_code": 400,
                    "detail": {"url": "http://127.0.0.1/admin"},
                },
                {
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                    "detail": None,
                },
            ]
        }
    }
