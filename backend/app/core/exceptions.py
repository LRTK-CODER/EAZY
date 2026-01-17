"""
Active Scan 커스텀 예외 클래스.

Usage:
    from app.core.exceptions import TargetNotFoundError, DuplicateScanError

Example:
    try:
        target = await session.get(Target, target_id)
        if not target:
            raise TargetNotFoundError(target_id=target_id)
    except ScanError as e:
        # Use global exception handler in main.py
        raise
"""

from typing import Any


class ScanError(Exception):
    """Active Scan 관련 기본 예외 클래스.

    모든 스캔 관련 예외의 부모 클래스.
    status_code와 error_code 속성을 통해 HTTP 응답 매핑을 지원합니다.
    """

    status_code: int = 500
    error_code: str = "SCAN_ERROR"

    def __init__(self, message: str = "Scan error occurred"):
        self.message = message
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to ErrorResponse-compatible dict."""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "detail": self._get_detail(),
        }

    def _get_detail(self) -> dict[str, Any] | None:
        """Override in subclasses to provide additional context."""
        return None


class TargetNotFoundError(ScanError):
    """대상 Target을 찾을 수 없을 때 발생하는 예외.

    HTTP 상태 코드: 404 Not Found
    """

    status_code: int = 404
    error_code: str = "TARGET_NOT_FOUND"

    def __init__(self, target_id: int):
        self.target_id = target_id
        super().__init__(f"Target not found: {target_id}")

    def _get_detail(self) -> dict[str, Any]:
        return {"target_id": self.target_id}


class DuplicateScanError(ScanError):
    """동일한 Target에 대해 이미 스캔이 진행 중일 때 발생하는 예외.

    HTTP 상태 코드: 409 Conflict
    """

    status_code: int = 409
    error_code: str = "DUPLICATE_SCAN"

    def __init__(self, target_id: int, existing_task_id: int | None = None):
        self.target_id = target_id
        self.existing_task_id = existing_task_id
        super().__init__(f"Scan already in progress for target: {target_id}")

    def _get_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {"target_id": self.target_id}
        if self.existing_task_id:
            detail["existing_task_id"] = self.existing_task_id
        return detail


class UnsafeUrlError(ScanError):
    """안전하지 않은 URL(내부망, localhost 등)에 접근 시도할 때 발생하는 예외.

    HTTP 상태 코드: 400 Bad Request
    """

    status_code: int = 400
    error_code: str = "UNSAFE_URL"

    def __init__(self, url: str, reason: str | None = None):
        self.url = url
        self.reason = reason
        super().__init__(f"Unsafe URL detected: {url}")

    def _get_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {"url": self.url}
        if self.reason:
            detail["reason"] = self.reason
        return detail
