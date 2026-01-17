"""
Core Constants 단위 테스트 - TDD Red Phase

상수 중앙화 검증을 위한 테스트.
"""


class TestCrawlerConstants:
    """크롤러 관련 상수 테스트"""

    def test_max_body_size_constant_exists(self):
        """MAX_BODY_SIZE 상수 존재 및 값 확인"""
        from app.core.constants import MAX_BODY_SIZE

        assert MAX_BODY_SIZE == 10 * 1024  # 10KB

    def test_page_timeout_constant_exists(self):
        """PAGE_TIMEOUT_MS 상수 존재 및 값 확인"""
        from app.core.constants import PAGE_TIMEOUT_MS

        assert PAGE_TIMEOUT_MS == 30000  # 30초


class TestWorkerConstants:
    """워커 관련 상수 테스트"""

    def test_lock_ttl_constant_exists(self):
        """LOCK_TTL 상수 존재 및 값 확인"""
        from app.core.constants import LOCK_TTL

        assert LOCK_TTL == 600  # 10분

    def test_cancellation_interval_constant_exists(self):
        """CANCELLATION_CHECK_INTERVAL 상수 존재 및 값 확인"""
        from app.core.constants import CANCELLATION_CHECK_INTERVAL

        assert CANCELLATION_CHECK_INTERVAL == 5.0  # 5초

    def test_lock_prefix_constant_exists(self):
        """LOCK_PREFIX 상수 존재 및 값 확인"""
        from app.core.constants import LOCK_PREFIX

        assert LOCK_PREFIX == "eazy:lock:"
