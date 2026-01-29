"""Cancellation port interface."""

from typing import Protocol


class ICancellation(Protocol):
    """취소 확인 인터페이스 - Redis cancel flag 확인"""

    async def is_cancelled(self, task_id: int) -> bool:
        """
        Task가 취소되었는지 확인.

        Args:
            task_id: 확인할 task ID

        Returns:
            True if cancelled
        """
        ...
