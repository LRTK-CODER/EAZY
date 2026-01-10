"""
Phase 2: 에러 분류 시스템

에러를 카테고리별로 분류하여 적절한 재시도 전략을 결정합니다.
- RETRYABLE: 일시적 네트워크 오류, 재시도 가능
- TRANSIENT: 서버 과부하, 대기 후 재시도
- PERMANENT: 잘못된 요청, 재시도 무의미
"""

from enum import Enum


class ErrorCategory(str, Enum):
    """에러 카테고리 분류"""

    RETRYABLE = "retryable"  # 네트워크 타임아웃, 연결 오류 등
    TRANSIENT = "transient"  # Rate limit, 503 등 일시적 서버 오류
    PERMANENT = "permanent"  # 404, 잘못된 데이터 등 재시도 무의미


def classify_error(error: Exception) -> ErrorCategory:
    """
    에러를 분류하여 적절한 카테고리를 반환합니다.

    Args:
        error: 분류할 예외 객체

    Returns:
        ErrorCategory: 에러 카테고리

    분류 기준:
    - PERMANENT: ValueError, TypeError, 404, "invalid", "malformed", "not found"
    - TRANSIENT: 429, 503, "rate limit", "service unavailable"
    - RETRYABLE: TimeoutError, ConnectionError, "timeout", "connection" (기본값)
    """
    error_str = str(error).lower()

    # PERMANENT 에러 (재시도 무의미)
    if isinstance(error, (ValueError, TypeError)):
        return ErrorCategory.PERMANENT

    if "404" in error_str or "not found" in error_str:
        return ErrorCategory.PERMANENT

    if "invalid" in error_str or "malformed" in error_str:
        return ErrorCategory.PERMANENT

    # TRANSIENT 에러 (대기 후 재시도)
    if "rate limit" in error_str or "429" in error_str:
        return ErrorCategory.TRANSIENT

    if "503" in error_str or "unavailable" in error_str:
        return ErrorCategory.TRANSIENT

    # RETRYABLE 에러 (즉시 재시도 가능)
    if isinstance(error, (TimeoutError, ConnectionError)):
        return ErrorCategory.RETRYABLE

    if "timeout" in error_str or "connection" in error_str:
        return ErrorCategory.RETRYABLE

    # 기본값: RETRYABLE (알 수 없는 에러는 재시도 시도)
    return ErrorCategory.RETRYABLE
