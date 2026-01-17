"""
CrawlerSettings 단위 테스트 - TDD Red Phase

pydantic-settings 기반 크롤러/워커 설정 검증.
Phase 5.1: pydantic-settings 적용
"""

import pytest
from pydantic import ValidationError


class TestCrawlerSettingsDefaults:
    """기본값 로드 테스트"""

    def test_loads_default_max_body_size(self):
        """CRAWLER_MAX_BODY_SIZE 기본값 10KB 로드"""
        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_MAX_BODY_SIZE == 10 * 1024  # 10KB

    def test_loads_default_page_timeout(self):
        """CRAWLER_PAGE_TIMEOUT_MS 기본값 30000ms 로드"""
        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_PAGE_TIMEOUT_MS == 30000  # 30초

    def test_loads_default_lock_ttl(self):
        """WORKER_LOCK_TTL 기본값 600초 로드"""
        from app.core.config import Settings

        settings = Settings()
        assert settings.WORKER_LOCK_TTL == 600  # 10분

    def test_loads_default_cancellation_interval(self):
        """WORKER_CANCELLATION_CHECK_INTERVAL 기본값 5.0초 로드"""
        from app.core.config import Settings

        settings = Settings()
        assert settings.WORKER_CANCELLATION_CHECK_INTERVAL == 5.0  # 5초


class TestCrawlerSettingsEnvVars:
    """환경변수 읽기 테스트"""

    def test_reads_max_body_size_from_env(self, monkeypatch):
        """CRAWLER_MAX_BODY_SIZE 환경변수 읽기"""
        monkeypatch.setenv("CRAWLER_MAX_BODY_SIZE", "20480")

        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_MAX_BODY_SIZE == 20480  # 20KB

    def test_reads_page_timeout_from_env(self, monkeypatch):
        """CRAWLER_PAGE_TIMEOUT_MS 환경변수 읽기"""
        monkeypatch.setenv("CRAWLER_PAGE_TIMEOUT_MS", "60000")

        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_PAGE_TIMEOUT_MS == 60000  # 60초

    def test_env_var_overrides_default(self, monkeypatch):
        """환경변수가 기본값을 오버라이드"""
        monkeypatch.setenv("WORKER_LOCK_TTL", "1200")

        from app.core.config import Settings

        settings = Settings()
        assert settings.WORKER_LOCK_TTL == 1200  # 20분


class TestCrawlerSettingsValidation:
    """값 검증 테스트"""

    def test_rejects_negative_max_body_size(self, monkeypatch):
        """음수 CRAWLER_MAX_BODY_SIZE 거부"""
        monkeypatch.setenv("CRAWLER_MAX_BODY_SIZE", "-1024")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_rejects_zero_page_timeout(self, monkeypatch):
        """0ms CRAWLER_PAGE_TIMEOUT_MS 거부"""
        monkeypatch.setenv("CRAWLER_PAGE_TIMEOUT_MS", "0")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_rejects_too_short_lock_ttl(self, monkeypatch):
        """60초 미만 WORKER_LOCK_TTL 거부"""
        monkeypatch.setenv("WORKER_LOCK_TTL", "30")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_rejects_invalid_type(self, monkeypatch):
        """정수 아닌 값 거부"""
        monkeypatch.setenv("CRAWLER_MAX_BODY_SIZE", "not_a_number")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_accepts_valid_range_values(self, monkeypatch):
        """유효 범위 내 값 수용"""
        monkeypatch.setenv("CRAWLER_MAX_BODY_SIZE", "51200")  # 50KB
        monkeypatch.setenv("CRAWLER_PAGE_TIMEOUT_MS", "120000")  # 2분
        monkeypatch.setenv("WORKER_LOCK_TTL", "900")  # 15분

        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_MAX_BODY_SIZE == 51200
        assert settings.CRAWLER_PAGE_TIMEOUT_MS == 120000
        assert settings.WORKER_LOCK_TTL == 900


class TestCrawlerSettingsTypeCoercion:
    """타입 변환 테스트"""

    def test_converts_string_to_int(self, monkeypatch):
        """문자열 -> 정수 변환"""
        monkeypatch.setenv("CRAWLER_MAX_BODY_SIZE", "15360")

        from app.core.config import Settings

        settings = Settings()
        assert settings.CRAWLER_MAX_BODY_SIZE == 15360
        assert isinstance(settings.CRAWLER_MAX_BODY_SIZE, int)

    def test_converts_string_to_float(self, monkeypatch):
        """문자열 -> 실수 변환"""
        monkeypatch.setenv("WORKER_CANCELLATION_CHECK_INTERVAL", "2.5")

        from app.core.config import Settings

        settings = Settings()
        assert settings.WORKER_CANCELLATION_CHECK_INTERVAL == 2.5
        assert isinstance(settings.WORKER_CANCELLATION_CHECK_INTERVAL, float)


class TestCrawlerSettingsIntegration:
    """통합 테스트"""

    def test_defaults_match_current_constants(self):
        """기본값이 현재 constants.py와 일치 (마이그레이션 안전성)"""
        from app.core.config import Settings

        settings = Settings()

        # 현재 constants.py의 값과 동일해야 함
        assert settings.CRAWLER_MAX_BODY_SIZE == 10 * 1024  # MAX_BODY_SIZE
        assert settings.CRAWLER_PAGE_TIMEOUT_MS == 30000  # PAGE_TIMEOUT_MS
        assert settings.WORKER_LOCK_TTL == 600  # LOCK_TTL
        assert settings.WORKER_CANCELLATION_CHECK_INTERVAL == 5.0  # CANCELLATION_CHECK_INTERVAL

    def test_settings_instance_is_usable(self):
        """설정 인스턴스가 정상 동작"""
        from app.core.config import settings

        # 싱글톤 인스턴스가 사용 가능해야 함
        assert hasattr(settings, "CRAWLER_MAX_BODY_SIZE")
        assert hasattr(settings, "CRAWLER_PAGE_TIMEOUT_MS")
        assert hasattr(settings, "WORKER_LOCK_TTL")
        assert hasattr(settings, "WORKER_CANCELLATION_CHECK_INTERVAL")

    def test_lock_prefix_remains_constant(self):
        """LOCK_PREFIX는 환경변수가 아닌 상수로 유지"""
        from app.core.constants import LOCK_PREFIX

        # LOCK_PREFIX는 constants.py에서 직접 가져와야 함 (환경변수 오버라이드 불필요)
        assert LOCK_PREFIX == "eazy:lock:"
