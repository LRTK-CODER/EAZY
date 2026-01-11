"""
Distributed Lock for EAZY worker infrastructure.

Phase 4: Scalability Improvement

Redis 기반 분산 잠금:
- SET NX EX로 원자적 획득
- Lua 스크립트로 안전한 해제
- Context Manager 지원
- TTL 연장 지원
"""

from __future__ import annotations

import uuid
from typing import Optional

from redis.asyncio import Redis


class LockAcquisitionError(Exception):
    """잠금 획득 실패 예외"""

    def __init__(self, lock_name: str, message: str = None):
        self.lock_name = lock_name
        self.message = message or f"Failed to acquire lock: {lock_name}"
        super().__init__(self.message)


class DistributedLock:
    """
    Redis 기반 분산 잠금.

    특징:
    - SET NX EX로 원자적 획득
    - Lua 스크립트로 안전한 해제
    - Context Manager 지원
    - TTL 연장 지원

    사용 예시:
        async with DistributedLock(redis, "target:123") as lock:
            # 이 블록 내에서 잠금 보장
            await do_work()

    Args:
        redis: Redis 클라이언트
        name: 잠금 이름 (예: "target:123")
        ttl: 잠금 만료 시간 (초)
        prefix: 키 접두사
    """

    # Lua 스크립트: 토큰 검증 후 삭제
    RELEASE_SCRIPT = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """

    # Lua 스크립트: 토큰 검증 후 TTL 연장
    EXTEND_SCRIPT = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('expire', KEYS[1], ARGV[2])
    else
        return 0
    end
    """

    def __init__(
        self, redis: Redis, name: str, ttl: int = 300, prefix: str = "eazy:lock:"
    ):
        """
        Args:
            redis: Redis 클라이언트
            name: 잠금 이름 (예: "target:123")
            ttl: 잠금 만료 시간 (초), 기본 5분
            prefix: 키 접두사
        """
        self.redis = redis
        self.name = name
        self.lock_key = f"{prefix}{name}"
        self.ttl = ttl
        self.token = str(uuid.uuid4())
        self._acquired = False

    async def acquire(self) -> bool:
        """
        잠금 획득 시도.

        Returns:
            True: 획득 성공
            False: 이미 다른 클라이언트가 점유 중
        """
        result = await self.redis.set(
            self.lock_key, self.token, nx=True, ex=self.ttl  # 존재하지 않을 때만
        )
        self._acquired = result is not None
        return self._acquired

    async def release(self) -> bool:
        """
        잠금 해제 (본인 토큰만).

        Returns:
            True: 성공적으로 해제
            False: 이미 만료되었거나 다른 클라이언트의 잠금
        """
        if not self._acquired:
            return False

        result = await self.redis.eval(
            self.RELEASE_SCRIPT, 1, self.lock_key, self.token
        )
        self._acquired = False
        return result == 1

    async def extend(self, additional_ttl: Optional[int] = None) -> bool:
        """
        잠금 TTL 연장.

        Args:
            additional_ttl: 연장할 시간 (초), None이면 원래 TTL 사용

        Returns:
            True: 연장 성공
            False: 잠금이 만료되었거나 다른 클라이언트의 잠금
        """
        ttl = additional_ttl or self.ttl
        result = await self.redis.eval(
            self.EXTEND_SCRIPT, 1, self.lock_key, self.token, str(ttl)
        )
        return result == 1

    async def is_owned(self) -> bool:
        """현재 이 인스턴스가 잠금을 소유하고 있는지 확인."""
        current_token = await self.redis.get(self.lock_key)
        return current_token == self.token

    async def __aenter__(self) -> "DistributedLock":
        """Context Manager 진입 시 잠금 획득."""
        if not await self.acquire():
            raise LockAcquisitionError(self.name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context Manager 종료 시 잠금 해제."""
        await self.release()
