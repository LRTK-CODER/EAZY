"""
커스텀 예외 클래스 단위 테스트 - TDD Red Phase

Active Scan 관련 예외 계층 구조 검증.
"""

import pytest


class TestScanErrorBase:
    """ScanError 기본 예외 클래스 테스트"""

    def test_scan_error_is_base_exception(self):
        """ScanError가 Exception을 상속하는지 확인"""
        from app.core.exceptions import ScanError

        assert issubclass(ScanError, Exception)

    def test_scan_error_can_be_raised(self):
        """ScanError를 raise 할 수 있는지 확인"""
        from app.core.exceptions import ScanError

        with pytest.raises(ScanError):
            raise ScanError("Test error")

    def test_scan_error_has_status_code(self):
        """ScanError가 status_code 속성을 가지는지 확인"""
        from app.core.exceptions import ScanError

        error = ScanError("Test error")
        assert hasattr(error, "status_code")
        assert error.status_code == 500  # 기본값


class TestTargetNotFoundError:
    """TargetNotFoundError 테스트"""

    def test_target_not_found_error_inheritance(self):
        """TargetNotFoundError가 ScanError를 상속하는지 확인"""
        from app.core.exceptions import ScanError, TargetNotFoundError

        assert issubclass(TargetNotFoundError, ScanError)

    def test_target_not_found_error_stores_target_id(self):
        """TargetNotFoundError가 target_id를 저장하는지 확인"""
        from app.core.exceptions import TargetNotFoundError

        error = TargetNotFoundError(target_id=123)
        assert error.target_id == 123

    def test_target_not_found_error_message_formatting(self):
        """TargetNotFoundError 메시지 포맷 확인"""
        from app.core.exceptions import TargetNotFoundError

        error = TargetNotFoundError(target_id=456)
        assert "456" in str(error)
        assert "not found" in str(error).lower()

    def test_target_not_found_error_status_code(self):
        """TargetNotFoundError status_code가 404인지 확인"""
        from app.core.exceptions import TargetNotFoundError

        error = TargetNotFoundError(target_id=1)
        assert error.status_code == 404


class TestDuplicateScanError:
    """DuplicateScanError 테스트"""

    def test_duplicate_scan_error_inheritance(self):
        """DuplicateScanError가 ScanError를 상속하는지 확인"""
        from app.core.exceptions import DuplicateScanError, ScanError

        assert issubclass(DuplicateScanError, ScanError)

    def test_duplicate_scan_error_stores_target_id(self):
        """DuplicateScanError가 target_id를 저장하는지 확인"""
        from app.core.exceptions import DuplicateScanError

        error = DuplicateScanError(target_id=789)
        assert error.target_id == 789

    def test_duplicate_scan_error_message_formatting(self):
        """DuplicateScanError 메시지 포맷 확인"""
        from app.core.exceptions import DuplicateScanError

        error = DuplicateScanError(target_id=321)
        assert "321" in str(error)

    def test_duplicate_scan_error_status_code(self):
        """DuplicateScanError status_code가 409인지 확인"""
        from app.core.exceptions import DuplicateScanError

        error = DuplicateScanError(target_id=1)
        assert error.status_code == 409


class TestUnsafeUrlError:
    """UnsafeUrlError 테스트"""

    def test_unsafe_url_error_inheritance(self):
        """UnsafeUrlError가 ScanError를 상속하는지 확인"""
        from app.core.exceptions import ScanError, UnsafeUrlError

        assert issubclass(UnsafeUrlError, ScanError)

    def test_unsafe_url_error_stores_url(self):
        """UnsafeUrlError가 url을 저장하는지 확인"""
        from app.core.exceptions import UnsafeUrlError

        error = UnsafeUrlError(url="http://127.0.0.1/admin")
        assert error.url == "http://127.0.0.1/admin"

    def test_unsafe_url_error_message_formatting(self):
        """UnsafeUrlError 메시지 포맷 확인"""
        from app.core.exceptions import UnsafeUrlError

        error = UnsafeUrlError(url="file:///etc/passwd")
        assert "file:///etc/passwd" in str(error)

    def test_unsafe_url_error_status_code(self):
        """UnsafeUrlError status_code가 400인지 확인"""
        from app.core.exceptions import UnsafeUrlError

        error = UnsafeUrlError(url="http://localhost")
        assert error.status_code == 400


class TestExceptionCatching:
    """예외 catch 시나리오 테스트"""

    def test_catch_target_not_found_as_scan_error(self):
        """TargetNotFoundError를 ScanError로 catch 가능한지 확인"""
        from app.core.exceptions import ScanError, TargetNotFoundError

        try:
            raise TargetNotFoundError(target_id=1)
        except ScanError as e:
            assert isinstance(e, TargetNotFoundError)
            assert e.status_code == 404

    def test_catch_duplicate_scan_as_scan_error(self):
        """DuplicateScanError를 ScanError로 catch 가능한지 확인"""
        from app.core.exceptions import DuplicateScanError, ScanError

        try:
            raise DuplicateScanError(target_id=1)
        except ScanError as e:
            assert isinstance(e, DuplicateScanError)
            assert e.status_code == 409

    def test_catch_unsafe_url_as_scan_error(self):
        """UnsafeUrlError를 ScanError로 catch 가능한지 확인"""
        from app.core.exceptions import ScanError, UnsafeUrlError

        try:
            raise UnsafeUrlError(url="http://localhost")
        except ScanError as e:
            assert isinstance(e, UnsafeUrlError)
            assert e.status_code == 400
