"""ScanProfile Enum 테스트.

TDD RED Phase: ScanProfile 구현 전 실패해야 하는 테스트.
"""


class TestScanProfileValues:
    """ScanProfile enum 값 테스트."""

    def test_scan_profile_has_quick_value(self):
        """QUICK 프로필이 존재하는지 확인."""
        from app.services.discovery.models import ScanProfile

        assert hasattr(ScanProfile, "QUICK")
        assert ScanProfile.QUICK.value == "quick"

    def test_scan_profile_has_standard_value(self):
        """STANDARD 프로필이 존재하는지 확인."""
        from app.services.discovery.models import ScanProfile

        assert hasattr(ScanProfile, "STANDARD")
        assert ScanProfile.STANDARD.value == "standard"

    def test_scan_profile_has_full_value(self):
        """FULL 프로필이 존재하는지 확인."""
        from app.services.discovery.models import ScanProfile

        assert hasattr(ScanProfile, "FULL")
        assert ScanProfile.FULL.value == "full"

    def test_scan_profile_values_are_distinct(self):
        """모든 프로필 값이 서로 다른지 확인."""
        from app.services.discovery.models import ScanProfile

        values = [p.value for p in ScanProfile]
        assert len(values) == len(set(values))
        assert len(values) == 3


class TestScanProfileStrEnum:
    """ScanProfile이 str, Enum 상속인지 테스트."""

    def test_scan_profile_is_str_enum(self):
        """str과 Enum을 상속하는지 확인."""
        from enum import Enum

        from app.services.discovery.models import ScanProfile

        assert issubclass(ScanProfile, str)
        assert issubclass(ScanProfile, Enum)

    def test_scan_profile_can_be_used_as_string(self):
        """문자열처럼 사용 가능한지 확인."""
        from app.services.discovery.models import ScanProfile

        # str(Enum)과 직접 비교 - str, Enum 상속으로 동등성 비교 가능
        assert ScanProfile.QUICK == "quick"
        # .value를 사용하여 문자열 값 접근
        assert ScanProfile.STANDARD.value == "standard"
        assert f"Profile: {ScanProfile.STANDARD.value}" == "Profile: standard"


class TestScanProfileDefault:
    """기본값 관련 테스트."""

    def test_default_profile_constant_exists(self):
        """기본 프로필 상수가 존재하는지 확인."""
        from app.services.discovery.models import DEFAULT_SCAN_PROFILE, ScanProfile

        assert DEFAULT_SCAN_PROFILE == ScanProfile.STANDARD

    def test_can_use_as_function_default(self):
        """함수 기본값으로 사용 가능한지 확인."""
        from app.services.discovery.models import ScanProfile

        def scan(profile: ScanProfile = ScanProfile.STANDARD) -> str:
            return profile.value

        assert scan() == "standard"
        assert scan(ScanProfile.QUICK) == "quick"
