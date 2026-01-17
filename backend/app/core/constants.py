"""
Central constants for EAZY backend.

Phase 5.1: pydantic-settings 통합
- 환경변수로 오버라이드 가능한 값은 Settings에서 가져옴
- 변경 불필요한 상수(LOCK_PREFIX)는 그대로 유지

Usage:
    from app.core.constants import MAX_BODY_SIZE, LOCK_TTL

    # 또는 직접 settings 사용 (권장):
    from app.core.config import settings
    settings.CRAWLER_MAX_BODY_SIZE
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
