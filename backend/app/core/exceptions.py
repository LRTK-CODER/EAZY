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
        raise HTTPException(status_code=e.status_code, detail=str(e))
"""


class ScanError(Exception):
    """Active Scan 관련 기본 예외 클래스.

    모든 스캔 관련 예외의 부모 클래스.
    status_code 속성을 통해 HTTP 상태 코드 매핑을 지원합니다.
    """

    status_code: int = 500

    def __init__(self, message: str = "Scan error occurred"):
        self.message = message
        super().__init__(self.message)


class TargetNotFoundError(ScanError):
    """대상 Target을 찾을 수 없을 때 발생하는 예외.

    HTTP 상태 코드: 404 Not Found
    """

    status_code: int = 404

    def __init__(self, target_id: int):
        self.target_id = target_id
        super().__init__(f"Target not found: {target_id}")


class DuplicateScanError(ScanError):
    """동일한 Target에 대해 이미 스캔이 진행 중일 때 발생하는 예외.

    HTTP 상태 코드: 409 Conflict
    """

    status_code: int = 409

    def __init__(self, target_id: int):
        self.target_id = target_id
        super().__init__(f"Scan already in progress for target: {target_id}")


class UnsafeUrlError(ScanError):
    """안전하지 않은 URL(내부망, localhost 등)에 접근 시도할 때 발생하는 예외.

    HTTP 상태 코드: 400 Bad Request
    """

    status_code: int = 400

    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Unsafe URL detected: {url}")
