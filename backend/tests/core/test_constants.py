"""
Core Constants 단위 테스트 - TDD Red Phase

상수 중앙화 검증을 위한 테스트.
"""

import pytest


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


class TestResourceTypeConstants:
    """Resource Type 상수 및 헬퍼 함수 테스트 (Phase 1 BLUE)"""

    def test_api_resource_types_constant_exists(self):
        """API_RESOURCE_TYPES 상수 존재 확인"""
        from app.core.constants import API_RESOURCE_TYPES

        assert "xhr" in API_RESOURCE_TYPES
        assert "fetch" in API_RESOURCE_TYPES
        assert len(API_RESOURCE_TYPES) == 2

    def test_non_api_resource_types_constant_exists(self):
        """NON_API_RESOURCE_TYPES 상수 존재 확인"""
        from app.core.constants import NON_API_RESOURCE_TYPES

        assert "image" in NON_API_RESOURCE_TYPES
        assert "stylesheet" in NON_API_RESOURCE_TYPES
        assert "font" in NON_API_RESOURCE_TYPES


class TestIsApiRequest:
    """is_api_request() 헬퍼 함수 테스트 (Phase 1 BLUE)"""

    @pytest.mark.parametrize(
        "resource_type,expected",
        [
            # API 요청 (True)
            ("xhr", True),
            ("fetch", True),
            # 비-API 요청 (False)
            ("document", False),
            ("script", False),
            ("stylesheet", False),
            ("image", False),
            ("font", False),
            ("media", False),
            # 엣지 케이스 (False)
            ("", False),
            ("XHR", False),  # 대소문자 구분
            ("FETCH", False),  # 대소문자 구분
            ("unknown", False),
        ],
    )
    def test_is_api_request(self, resource_type: str, expected: bool):
        """resource_type에 따른 API 요청 판별 테스트"""
        from app.core.constants import is_api_request

        assert is_api_request(resource_type) == expected

    def test_is_api_request_with_xhr(self):
        """XHR 요청은 True 반환"""
        from app.core.constants import is_api_request

        assert is_api_request("xhr") is True

    def test_is_api_request_with_fetch(self):
        """Fetch 요청은 True 반환"""
        from app.core.constants import is_api_request

        assert is_api_request("fetch") is True

    def test_is_api_request_with_document(self):
        """Document 요청은 False 반환"""
        from app.core.constants import is_api_request

        assert is_api_request("document") is False

    def test_is_api_request_with_empty_string(self):
        """빈 문자열은 False 반환"""
        from app.core.constants import is_api_request

        assert is_api_request("") is False
