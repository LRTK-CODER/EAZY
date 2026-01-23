"""DiscoveryContext 데이터 클래스 테스트.

TDD RED Phase: DiscoveryContext 구현 전 실패해야 하는 테스트.
"""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

import pytest


class TestDiscoveryContextCreation:
    """DiscoveryContext 생성 테스트."""

    def test_create_with_required_fields(self):
        """필수 필드로 생성 가능한지 확인."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        mock_http_client = MagicMock()
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
        )

        assert context.target_url == "https://example.com"
        assert context.profile == ScanProfile.STANDARD
        assert context.http_client is mock_http_client

    def test_optional_fields_have_defaults(self):
        """선택적 필드에 기본값이 있는지 확인."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.QUICK,
            http_client=MagicMock(),
        )

        assert context.timeout == 30.0
        assert context.max_depth == 3
        assert context.base_url == "https://example.com"
        assert context.crawl_data == {}

    def test_can_set_optional_fields(self):
        """선택적 필드 설정 가능한지 확인."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        crawl_data = {"links": ["https://example.com/page1"]}
        context = DiscoveryContext(
            target_url="https://example.com/path",
            profile=ScanProfile.FULL,
            http_client=MagicMock(),
            timeout=60.0,
            max_depth=5,
            base_url="https://example.com",
            crawl_data=crawl_data,
        )

        assert context.timeout == 60.0
        assert context.max_depth == 5
        assert context.base_url == "https://example.com"
        assert context.crawl_data == crawl_data


class TestDiscoveryContextImmutability:
    """불변성 테스트."""

    def test_cannot_modify_target_url(self):
        """target_url 수정 시 에러 발생."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )

        with pytest.raises(FrozenInstanceError):
            context.target_url = "https://other.com"

    def test_cannot_modify_profile(self):
        """profile 수정 시 에러 발생."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )

        with pytest.raises(FrozenInstanceError):
            context.profile = ScanProfile.FULL


class TestDiscoveryContextValidation:
    """유효성 검사 테스트."""

    def test_valid_https_url(self):
        """HTTPS URL 유효성 확인."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )
        assert context.target_url == "https://example.com"

    def test_valid_http_url(self):
        """HTTP URL 유효성 확인."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        context = DiscoveryContext(
            target_url="http://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )
        assert context.target_url == "http://example.com"


class TestDiscoveryContextHelpers:
    """헬퍼 메서드 테스트."""

    def test_is_quick_profile(self):
        """is_quick_profile 메서드."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        quick_context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.QUICK,
            http_client=MagicMock(),
        )
        standard_context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )

        assert quick_context.is_quick_profile() is True
        assert standard_context.is_quick_profile() is False

    def test_is_full_profile(self):
        """is_full_profile 메서드."""
        from app.services.discovery.models import DiscoveryContext, ScanProfile

        full_context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=MagicMock(),
        )
        standard_context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=MagicMock(),
        )

        assert full_context.is_full_profile() is True
        assert standard_context.is_full_profile() is False
