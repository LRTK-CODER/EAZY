"""Discovery 서비스 모델 정의.

스캔 프로필, 발견된 자산, 컨텍스트 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from app.core.utils import utc_now


class ScanProfile(str, Enum):
    """스캔 프로필 정의.

    QUICK: 빠른 스캔 (기본 검사만)
    STANDARD: 표준 스캔 (일반적인 검사)
    FULL: 전체 스캔 (모든 검사 수행)
    """

    QUICK = "quick"
    STANDARD = "standard"
    FULL = "full"


# 기본 스캔 프로필
DEFAULT_SCAN_PROFILE: ScanProfile = ScanProfile.STANDARD


@dataclass(frozen=True)
class DiscoveredAsset:
    """발견된 자산 정보.

    불변 데이터 클래스로, URL과 asset_type을 기준으로 중복을 판별합니다.

    Attributes:
        url: 발견된 URL
        asset_type: 자산 유형 (endpoint, form, page 등)
        source: 발견 소스 (network, html, js 등)
        metadata: 추가 메타데이터
        discovered_at: 발견 시각

    Example:
        >>> asset = DiscoveredAsset(
        ...     url="https://example.com/api",
        ...     asset_type="endpoint",
        ...     source="network",
        ... )
        >>> asset in asset_set  # 중복 체크 가능
    """

    url: str
    asset_type: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)
    discovered_at: datetime = field(default_factory=utc_now, compare=False, hash=False)

    def __hash__(self) -> int:
        """URL과 asset_type 기준 해시."""
        return hash((self.url, self.asset_type))

    def __eq__(self, other: object) -> bool:
        """URL과 asset_type 기준 동등성 비교."""
        if not isinstance(other, DiscoveredAsset):
            return False
        return self.url == other.url and self.asset_type == other.asset_type


@dataclass(frozen=True)
class DiscoveryContext:
    """Discovery 실행 컨텍스트.

    Discovery 모듈 실행에 필요한 모든 정보를 불변 객체로 제공합니다.

    Attributes:
        target_url: 스캔 대상 URL
        profile: 스캔 프로필
        http_client: HTTP 클라이언트 (httpx.AsyncClient)
        timeout: 요청 타임아웃 (초)
        max_depth: 최대 탐색 깊이
        base_url: 기본 URL (scope 판단용)
        crawl_data: 크롤링 결과 데이터

    Example:
        >>> context = DiscoveryContext(
        ...     target_url="https://example.com",
        ...     profile=ScanProfile.STANDARD,
        ...     http_client=http_client,
        ... )
    """

    target_url: str
    profile: ScanProfile
    http_client: Any  # httpx.AsyncClient - Any to avoid import dependency
    timeout: float = 30.0
    max_depth: int = 3
    base_url: str = ""
    crawl_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """초기화 후 처리 - base_url 기본값 설정."""
        if not self.base_url:
            # frozen=True이므로 object.__setattr__ 사용
            object.__setattr__(self, "base_url", self.target_url)

    def is_quick_profile(self) -> bool:
        """QUICK 프로필인지 확인."""
        return self.profile == ScanProfile.QUICK

    def is_full_profile(self) -> bool:
        """FULL 프로필인지 확인."""
        return self.profile == ScanProfile.FULL
