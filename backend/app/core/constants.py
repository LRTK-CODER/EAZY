"""
Central constants for EAZY backend.

Usage:
    from app.core.constants import MAX_BODY_SIZE, LOCK_TTL

Example:
    if len(body) > MAX_BODY_SIZE:
        body = body[:MAX_BODY_SIZE] + "... [TRUNCATED]"
"""

# === Crawler Constants ===
MAX_BODY_SIZE: int = 10 * 1024  # 10KB - HTTP body 크기 제한
PAGE_TIMEOUT_MS: int = 30000  # 30초 - 페이지 로드 타임아웃 (밀리초)

# === Worker Constants ===
LOCK_TTL: int = 600  # 10분 - 분산 락 TTL (초)
CANCELLATION_CHECK_INTERVAL: float = 5.0  # 5초 - 작업 취소 확인 간격
LOCK_PREFIX: str = "eazy:lock:"  # Redis 락 키 접두사
