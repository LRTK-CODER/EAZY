"""
Domain 계층의 Scope 검증 서비스.

기존 ScopeFilter를 래핑하여 Domain 계층에서 사용 가능하게 합니다.
"""

from typing import TYPE_CHECKING, List, Optional, Protocol

from app.services.scope_filter import ScopeFilter

if TYPE_CHECKING:
    from app.models.target import TargetScope


class TargetLike(Protocol):
    """Target 모델과 호환되는 Protocol"""

    url: str
    scope: "TargetScope"


class ScopeChecker:
    """
    Domain 계층의 Scope 검증 서비스.

    기존 ScopeFilter를 래핑하여 Domain 계층에서 사용 가능하게 합니다.
    """

    def is_in_scope(self, url: Optional[str], target: Optional[TargetLike]) -> bool:
        """
        URL이 Target의 scope 내에 있는지 검증.

        Args:
            url: 검증할 URL
            target: Target 객체 (url, scope 속성 필요)

        Returns:
            True if URL is in scope
        """
        if not url or not target:
            return False

        scope_filter = ScopeFilter(target.url, target.scope)
        return scope_filter.is_in_scope(url)

    def filter_urls(self, urls: List[str], target: TargetLike) -> List[str]:
        """
        URL 목록에서 scope 내 URL만 필터링.

        Args:
            urls: 검증할 URL 목록
            target: Target 객체

        Returns:
            scope 내 URL 목록
        """
        if not target:
            return []

        scope_filter = ScopeFilter(target.url, target.scope)
        return scope_filter.filter_urls(urls)
