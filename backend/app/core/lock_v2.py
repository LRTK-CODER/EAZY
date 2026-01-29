"""
Distributed Lock V2 with Fence Token for EAZY worker infrastructure.

Phase 1: Infrastructure Foundation

Redis 기반 분산 잠금 with fence token:
- Fence token으로 stale lock 방지
- 단조 증가 토큰 (monotonically increasing)
- 레벨별 락킹 (TASK, URL, TARGET)
- TTL 기반 자동 만료
- 컨텍스트 매니저 지원
- Lua 스크립트로 원자적 연산
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any, Dict, Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class LockLevel(Enum):
    """Lock 레벨 (세분화된 락킹)"""

    TASK = "task"
    URL = "url"
    TARGET = "target"


class DistributedLockV2:
    """
    분산 락 구현 with Fence Token.

    특징:
    - Fence token으로 stale lock 방지
    - 단조 증가 토큰 (monotonically increasing)
    - 레벨별 락킹 (TASK, URL, TARGET)
    - TTL 기반 자동 만료
    - 컨텍스트 매니저 지원

    사용 예시:
        async with DistributedLockV2(redis, "task-123", LockLevel.TASK) as token:
            # 이 블록 내에서 잠금 보장
            await do_work(token)
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
    RENEW_SCRIPT = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('expire', KEYS[1], ARGV[2])
    else
        return 0
    end
    """

    # Global fence token counter key
    TOKEN_COUNTER_KEY = "lock:token_counter"

    def __init__(
        self,
        redis: Redis,
        resource_id: str,
        level: LockLevel,
        ttl_seconds: int = 30,
    ):
        """
        Args:
            redis: Redis connection
            resource_id: 리소스 ID (task ID, URL, target ID 등)
            level: Lock 레벨
            ttl_seconds: TTL (초), must be > 0

        Raises:
            ValueError: ttl_seconds <= 0 또는 resource_id가 빈 문자열인 경우
        """
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        if not resource_id or not resource_id.strip():
            raise ValueError("resource_id cannot be empty")

        self.redis = redis
        self.resource_id = resource_id
        self.level = level
        self.ttl_seconds = ttl_seconds

        # Lock key: lock:{level}:{resource_id}
        self.lock_key = f"lock:{level.value}:{resource_id}"

        # 현재 획득한 토큰 (None이면 미획득)
        self._acquired_token: Optional[int] = None

        logger.debug(
            f"Initialized DistributedLockV2: key={self.lock_key}, ttl={ttl_seconds}s"
        )

    async def acquire(
        self,
        timeout: Optional[float] = None,
        retry_interval: float = 0.1,
    ) -> Optional[int]:
        """
        락 획득 시도.

        Args:
            timeout: 최대 대기 시간 (초). None이면 즉시 반환.
            retry_interval: 재시도 간격 (초)

        Returns:
            성공 시 fence token (int), 실패 시 None
        """
        start_time: Optional[float] = (
            asyncio.get_event_loop().time() if timeout is not None else None
        )

        while True:
            try:
                # 1. Generate fence token (monotonically increasing)
                fence_token: int = await self.redis.incr(self.TOKEN_COUNTER_KEY)

                # 2. Try to acquire lock with SET NX EX
                result = await self.redis.set(
                    self.lock_key,
                    str(fence_token),
                    nx=True,  # Only set if not exists
                    ex=self.ttl_seconds,  # Expire time in seconds
                )

                if result:
                    self._acquired_token = fence_token
                    logger.info(
                        f"Lock acquired: key={self.lock_key}, token={fence_token}"
                    )
                    return int(fence_token)

                # 3. If timeout is None, return immediately
                if timeout is None:
                    logger.debug(f"Lock not available: key={self.lock_key}")
                    return None

                # 4. Check timeout
                if start_time is not None and timeout is not None:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= timeout:
                        logger.warning(
                            f"Lock acquisition timeout: key={self.lock_key}, "
                            f"timeout={timeout}s"
                        )
                        return None

                # 5. Wait and retry
                await asyncio.sleep(retry_interval)

            except Exception as e:
                logger.error(f"Error acquiring lock {self.lock_key}: {e}")
                raise

    async def release(self, token: int) -> bool:
        """
        락 해제.

        Args:
            token: acquire()에서 받은 fence token

        Returns:
            성공 시 True, 실패 시 False (토큰 불일치 또는 이미 만료)
        """
        try:
            result: int = await self.redis.eval(  # type: ignore[misc]
                self.RELEASE_SCRIPT,
                1,  # number of keys
                self.lock_key,  # KEYS[1]
                str(token),  # ARGV[1]
            )
            success = bool(result)

            if success:
                logger.info(f"Lock released: key={self.lock_key}, token={token}")
                if self._acquired_token == token:
                    self._acquired_token = None
            else:
                logger.warning(
                    f"Lock release failed: key={self.lock_key}, token={token} "
                    "(token mismatch or expired)"
                )
            return success
        except Exception as e:
            logger.error(f"Error releasing lock {self.lock_key}: {e}")
            return False

    async def renew(self, token: int, ttl_seconds: Optional[int] = None) -> bool:
        """
        TTL 갱신.

        Args:
            token: acquire()에서 받은 fence token
            ttl_seconds: 새 TTL (기본값: 생성자에서 지정한 값)

        Returns:
            성공 시 True, 실패 시 False
        """
        if ttl_seconds is None:
            ttl_seconds = self.ttl_seconds

        try:
            result: int = await self.redis.eval(  # type: ignore[misc]
                self.RENEW_SCRIPT,
                1,  # number of keys
                self.lock_key,  # KEYS[1]
                str(token),  # ARGV[1]
                str(ttl_seconds),  # ARGV[2]
            )
            success = bool(result)

            if success:
                logger.info(
                    f"Lock renewed: key={self.lock_key}, token={token}, "
                    f"ttl={ttl_seconds}s"
                )
            else:
                logger.warning(
                    f"Lock renewal failed: key={self.lock_key}, token={token} "
                    "(token mismatch or expired)"
                )
            return success
        except Exception as e:
            logger.error(f"Error renewing lock {self.lock_key}: {e}")
            return False

    async def get_info(self) -> Dict[str, Any]:
        """
        락 정보 조회.

        Returns:
            {
                "resource_id": str,
                "level": LockLevel,
                "current_token": int or None,
                "ttl": int or None,
                "is_locked": bool,
            }
        """
        try:
            # Get current token
            token_bytes = await self.redis.get(self.lock_key)
            current_token = None

            if token_bytes is not None:
                current_token = int(token_bytes.decode())

            # Get TTL
            ttl = await self.redis.ttl(self.lock_key)

            # TTL -2 means key doesn't exist, -1 means no expiration
            if ttl == -2:
                ttl = None

            is_locked = token_bytes is not None

            return {
                "resource_id": self.resource_id,
                "level": self.level,
                "current_token": current_token,
                "ttl": ttl,
                "is_locked": is_locked,
            }

        except Exception as e:
            logger.error(f"Error getting lock info {self.lock_key}: {e}")
            return {
                "resource_id": self.resource_id,
                "level": self.level,
                "current_token": None,
                "ttl": None,
                "is_locked": False,
            }

    async def __aenter__(self) -> int:
        """
        컨텍스트 매니저 진입.

        Returns:
            fence token

        Raises:
            RuntimeError: 락 획득 실패 시
        """
        token = await self.acquire()

        if token is None:
            raise RuntimeError(
                f"Failed to acquire lock: key={self.lock_key}, "
                f"level={self.level.value}, resource_id={self.resource_id}"
            )

        return token

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """컨텍스트 매니저 종료. 자동으로 release 호출."""
        if self._acquired_token is not None:
            await self.release(self._acquired_token)
