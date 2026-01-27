"""
Central constants for EAZY backend.

Phase 5.1: pydantic-settings 통합
- 환경변수로 오버라이드 가능한 값은 Settings에서 가져옴
- 변경 불필요한 상수(LOCK_PREFIX)는 그대로 유지

Usage:
    from app.core.constants import MAX_BODY_SIZE, LOCK_TTL, is_api_request

    # 또는 직접 settings 사용 (권장):
    from app.core.config import settings
    settings.CRAWLER_MAX_BODY_SIZE

    # Resource type 헬퍼 함수:
    if is_api_request(resource_type):
        # XHR 또는 Fetch 요청 처리
"""

from typing import Final

from app.core.config import settings

# === Crawler Constants (from Settings - 환경변수 오버라이드 가능) ===
MAX_BODY_SIZE: int = settings.CRAWLER_MAX_BODY_SIZE
PAGE_TIMEOUT_MS: int = settings.CRAWLER_PAGE_TIMEOUT_MS

# === Worker Constants (from Settings - 환경변수 오버라이드 가능) ===
LOCK_TTL: int = settings.WORKER_LOCK_TTL
CANCELLATION_CHECK_INTERVAL: float = settings.WORKER_CANCELLATION_CHECK_INTERVAL

# === True Constants (변경 불필요 - 환경변수 오버라이드 불필요) ===
LOCK_PREFIX: Final[str] = "eazy:lock:"

# === Resource Type Constants (Phase 1: CrawlerService resource_type 캡처) ===
# Playwright request.resource_type 분류
API_RESOURCE_TYPES: Final[frozenset] = frozenset({"xhr", "fetch"})
NON_API_RESOURCE_TYPES: Final[frozenset] = frozenset(
    {"image", "stylesheet", "font", "media", "manifest"}
)


def is_api_request(resource_type: str) -> bool:
    """Check if the resource type indicates an API request (XHR/Fetch).

    Args:
        resource_type: Playwright request.resource_type value
            (e.g., "xhr", "fetch", "document", "script")

    Returns:
        True if resource_type is "xhr" or "fetch", False otherwise.

    Examples:
        >>> is_api_request("xhr")
        True
        >>> is_api_request("document")
        False
    """
    return resource_type in API_RESOURCE_TYPES


# === JavaScript Content Constants (Phase 2: JS 파일 content 수집) ===
MAX_JS_CONTENT_SIZE: int = 5 * 1024 * 1024  # 5MB 제한

# JavaScript Content-Type 식별자
JS_CONTENT_TYPES: Final[frozenset] = frozenset(
    {
        "application/javascript",
        "text/javascript",
        "application/x-javascript",
    }
)
