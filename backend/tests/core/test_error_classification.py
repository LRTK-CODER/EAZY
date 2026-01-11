"""
Phase 2 Day 1: 에러 분류 시스템 테스트

TDD RED 단계 - 이 테스트들은 errors.py와 retry.py 구현 전에 실패해야 함
"""

from unittest.mock import patch


class TestErrorCategory:
    """ErrorCategory Enum 테스트"""

    def test_error_category_has_retryable(self):
        """RETRYABLE 카테고리가 존재해야 함"""
        from app.core.errors import ErrorCategory

        assert hasattr(ErrorCategory, "RETRYABLE")
        assert ErrorCategory.RETRYABLE.value == "retryable"

    def test_error_category_has_permanent(self):
        """PERMANENT 카테고리가 존재해야 함"""
        from app.core.errors import ErrorCategory

        assert hasattr(ErrorCategory, "PERMANENT")
        assert ErrorCategory.PERMANENT.value == "permanent"

    def test_error_category_has_transient(self):
        """TRANSIENT 카테고리가 존재해야 함"""
        from app.core.errors import ErrorCategory

        assert hasattr(ErrorCategory, "TRANSIENT")
        assert ErrorCategory.TRANSIENT.value == "transient"


class TestClassifyError:
    """classify_error() 함수 테스트"""

    def test_classify_timeout_as_retryable(self):
        """TimeoutError는 RETRYABLE로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = TimeoutError("Connection timed out")
        result = classify_error(error)

        assert result == ErrorCategory.RETRYABLE

    def test_classify_connection_error_as_retryable(self):
        """ConnectionError는 RETRYABLE로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = ConnectionError("Connection refused")
        result = classify_error(error)

        assert result == ErrorCategory.RETRYABLE

    def test_classify_timeout_string_as_retryable(self):
        """'timeout' 문자열을 포함한 에러는 RETRYABLE로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("Request timeout after 30 seconds")
        result = classify_error(error)

        assert result == ErrorCategory.RETRYABLE

    def test_classify_404_as_permanent(self):
        """404 에러는 PERMANENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("HTTP 404: Not Found")
        result = classify_error(error)

        assert result == ErrorCategory.PERMANENT

    def test_classify_not_found_as_permanent(self):
        """'not found' 문자열을 포함한 에러는 PERMANENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("Resource not found")
        result = classify_error(error)

        assert result == ErrorCategory.PERMANENT

    def test_classify_invalid_data_as_permanent(self):
        """ValueError는 PERMANENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = ValueError("Invalid URL format")
        result = classify_error(error)

        assert result == ErrorCategory.PERMANENT

    def test_classify_type_error_as_permanent(self):
        """TypeError는 PERMANENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = TypeError("Expected string, got int")
        result = classify_error(error)

        assert result == ErrorCategory.PERMANENT

    def test_classify_malformed_as_permanent(self):
        """'malformed' 문자열을 포함한 에러는 PERMANENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("Malformed JSON response")
        result = classify_error(error)

        assert result == ErrorCategory.PERMANENT

    def test_classify_rate_limit_as_transient(self):
        """Rate limit 에러는 TRANSIENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("Rate limit exceeded")
        result = classify_error(error)

        assert result == ErrorCategory.TRANSIENT

    def test_classify_429_as_transient(self):
        """HTTP 429 에러는 TRANSIENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("HTTP 429: Too Many Requests")
        result = classify_error(error)

        assert result == ErrorCategory.TRANSIENT

    def test_classify_503_as_transient(self):
        """HTTP 503 에러는 TRANSIENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("HTTP 503: Service Unavailable")
        result = classify_error(error)

        assert result == ErrorCategory.TRANSIENT

    def test_classify_service_unavailable_as_transient(self):
        """'service unavailable' 문자열을 포함한 에러는 TRANSIENT로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("The service is temporarily unavailable")
        result = classify_error(error)

        assert result == ErrorCategory.TRANSIENT

    def test_unknown_error_defaults_to_retryable(self):
        """알 수 없는 에러는 기본적으로 RETRYABLE로 분류되어야 함"""
        from app.core.errors import ErrorCategory, classify_error

        error = Exception("Some unknown error occurred")
        result = classify_error(error)

        assert result == ErrorCategory.RETRYABLE


class TestCalculateBackoff:
    """calculate_backoff() 함수 테스트"""

    def test_backoff_first_retry(self):
        """첫 번째 재시도는 BASE_DELAY 근처여야 함"""
        from app.core.retry import calculate_backoff, BASE_DELAY, JITTER_RANGE

        delay = calculate_backoff(0)

        # Jitter 범위 내에 있어야 함
        min_expected = BASE_DELAY * (1 - JITTER_RANGE)
        max_expected = BASE_DELAY * (1 + JITTER_RANGE)

        assert min_expected <= delay <= max_expected

    def test_backoff_increases_exponentially(self):
        """재시도 횟수에 따라 지수적으로 증가해야 함"""
        from app.core.retry import calculate_backoff

        # Jitter 제거하고 평균값 비교
        with patch("random.uniform", return_value=0):
            delay_0 = calculate_backoff(0)  # BASE_DELAY * 2^0 = 1
            delay_1 = calculate_backoff(1)  # BASE_DELAY * 2^1 = 2
            delay_2 = calculate_backoff(2)  # BASE_DELAY * 2^2 = 4

        assert delay_1 == delay_0 * 2
        assert delay_2 == delay_0 * 4

    def test_backoff_capped_at_max_delay(self):
        """MAX_DELAY를 초과하지 않아야 함"""
        from app.core.retry import calculate_backoff, MAX_DELAY, JITTER_RANGE

        # 아주 큰 재시도 횟수
        delay = calculate_backoff(100)

        # Jitter를 고려한 최대값
        max_with_jitter = MAX_DELAY * (1 + JITTER_RANGE)

        assert delay <= max_with_jitter

    def test_jitter_within_range(self):
        """Jitter가 지정된 범위 내에 있어야 함"""
        from app.core.retry import calculate_backoff, BASE_DELAY, JITTER_RANGE

        # 여러 번 실행하여 범위 확인
        for _ in range(100):
            delay = calculate_backoff(0)
            min_expected = BASE_DELAY * (1 - JITTER_RANGE)
            max_expected = BASE_DELAY * (1 + JITTER_RANGE)

            assert min_expected <= delay <= max_expected

    def test_jitter_produces_different_values(self):
        """Jitter로 인해 매번 다른 값이 나와야 함"""
        from app.core.retry import calculate_backoff

        delays = [calculate_backoff(1) for _ in range(10)]

        # 모든 값이 같지 않아야 함 (확률적으로 거의 불가능)
        assert len(set(delays)) > 1


class TestRetryConstants:
    """재시도 관련 상수 테스트"""

    def test_max_retries_is_defined(self):
        """MAX_RETRIES 상수가 정의되어 있어야 함"""
        from app.core.retry import MAX_RETRIES

        assert MAX_RETRIES == 3

    def test_base_delay_is_defined(self):
        """BASE_DELAY 상수가 정의되어 있어야 함"""
        from app.core.retry import BASE_DELAY

        assert BASE_DELAY == 1.0

    def test_max_delay_is_defined(self):
        """MAX_DELAY 상수가 정의되어 있어야 함"""
        from app.core.retry import MAX_DELAY

        assert MAX_DELAY == 60.0

    def test_jitter_range_is_defined(self):
        """JITTER_RANGE 상수가 정의되어 있어야 함"""
        from app.core.retry import JITTER_RANGE

        assert JITTER_RANGE == 0.5


class TestTaskRetryInfo:
    """TaskRetryInfo dataclass 테스트"""

    def test_task_retry_info_creation(self):
        """TaskRetryInfo를 생성할 수 있어야 함"""
        from app.core.retry import TaskRetryInfo

        info = TaskRetryInfo(task_id="test-123")

        assert info.task_id == "test-123"
        assert info.retry_count == 0
        assert info.last_error is None
        assert info.error_category is None
        assert info.next_retry_at is None

    def test_task_retry_info_with_values(self):
        """TaskRetryInfo에 값을 설정할 수 있어야 함"""
        from datetime import datetime
        from app.core.retry import TaskRetryInfo
        from app.core.errors import ErrorCategory

        now = datetime.now()
        info = TaskRetryInfo(
            task_id="test-456",
            retry_count=2,
            last_error="Connection refused",
            error_category=ErrorCategory.RETRYABLE,
            next_retry_at=now,
        )

        assert info.task_id == "test-456"
        assert info.retry_count == 2
        assert info.last_error == "Connection refused"
        assert info.error_category == ErrorCategory.RETRYABLE
        assert info.next_retry_at == now
