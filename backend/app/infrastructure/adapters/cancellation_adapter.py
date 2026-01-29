"""CancellationAdapter - Redis cancel flag를 ICancellation 포트에 맞게 어댑팅."""

from typing import Any


class CancellationAdapter:
    """Redis cancel flag를 ICancellation 포트에 맞게 어댑팅.

    Redis에서 task:{task_id}:cancel 키를 확인하여 취소 여부를 판단합니다.
    """

    def __init__(self, redis: Any):
        """CancellationAdapter 초기화.

        Args:
            redis: Redis 클라이언트
        """
        self._redis = redis

    async def is_cancelled(self, task_id: int) -> bool:
        """Task가 취소되었는지 확인.

        Args:
            task_id: 확인할 task ID

        Returns:
            True if cancel flag exists in Redis
        """
        cancel_key = f"task:{task_id}:cancel"
        cancel_flag = await self._redis.get(cancel_key)
        return cancel_flag is not None
