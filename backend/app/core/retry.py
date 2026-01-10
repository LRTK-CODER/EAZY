"""
Phase 2: 재시도 로직

Exponential Backoff with Jitter를 사용한 재시도 전략을 제공합니다.
"""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.errors import ErrorCategory


# 재시도 관련 상수
MAX_RETRIES: int = 3  # 최대 재시도 횟수
BASE_DELAY: float = 1.0  # 기본 대기 시간 (초)
MAX_DELAY: float = 60.0  # 최대 대기 시간 (초)
JITTER_RANGE: float = 0.5  # Jitter 범위 (±50%)


def calculate_backoff(retry_count: int) -> float:
    """
    Exponential Backoff with Jitter를 계산합니다.

    Args:
        retry_count: 현재 재시도 횟수 (0부터 시작)

    Returns:
        float: 대기 시간 (초)

    공식:
        delay = min(BASE_DELAY * 2^retry_count, MAX_DELAY)
        jitter = delay * random(-JITTER_RANGE, +JITTER_RANGE)
        final_delay = delay + jitter
    """
    # 지수적 증가 (최대값 제한)
    delay = min(BASE_DELAY * (2**retry_count), MAX_DELAY)

    # Jitter 추가 (동시 재시도 방지)
    jitter = delay * random.uniform(-JITTER_RANGE, JITTER_RANGE)

    return delay + jitter


@dataclass
class TaskRetryInfo:
    """작업 재시도 정보를 추적하는 데이터 클래스"""

    task_id: str
    retry_count: int = 0
    last_error: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    next_retry_at: Optional[datetime] = None

    def should_retry(self) -> bool:
        """재시도 가능 여부를 확인합니다."""
        if self.retry_count >= MAX_RETRIES:
            return False

        if self.error_category == ErrorCategory.PERMANENT:
            return False

        return True

    def increment_retry(self, error: Exception, category: ErrorCategory) -> None:
        """재시도 횟수를 증가시키고 에러 정보를 업데이트합니다."""
        self.retry_count += 1
        self.last_error = str(error)
        self.error_category = category

    def get_next_delay(self) -> float:
        """다음 재시도까지의 대기 시간을 계산합니다."""
        return calculate_backoff(self.retry_count)
