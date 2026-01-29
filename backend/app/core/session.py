"""
SessionManager - 안전한 세션 생명주기 관리.

Phase 1: Infrastructure Layer
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    pass


class SessionManager:
    """
    데이터베이스 세션 관리자.

    특징:
    - 자동 commit/rollback/close
    - Connection pool 설정
    - SAVEPOINT를 사용한 중첩 트랜잭션
    - 싱글톤 지원

    사용 예시:
        manager = SessionManager(database_url="...")
        async with manager.session() as session:
            # 자동 commit (성공 시) 또는 rollback (예외 시)
            await session.exec(...)
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 5,
        max_overflow: int = 5,
        echo: bool = False,
    ):
        self._database_url = database_url
        self._pool_size = pool_size
        self._max_overflow = max_overflow

        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            future=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def pool_size(self) -> int:
        """Connection pool 크기."""
        return self._pool_size

    @property
    def max_overflow(self) -> int:
        """최대 추가 연결 수."""
        return self._max_overflow

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        자동 commit/rollback/close 세션 컨텍스트.

        성공 시 자동 commit, 예외 시 자동 rollback.
        항상 close 호출.
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[None, None]:
        """
        SAVEPOINT를 사용한 중첩 트랜잭션.

        Args:
            session: 부모 세션

        사용 예시:
            async with manager.session() as session:
                async with manager.transaction(session):
                    # SAVEPOINT 내 작업
        """
        async with session.begin_nested():
            yield

    def create_session_factory(
        self, pool_size: int | None = None
    ) -> async_sessionmaker[AsyncSession]:
        """
        커스텀 pool_size로 새 세션 팩토리 생성.

        WorkerPool 등에서 별도 pool_size가 필요할 때 사용.
        """
        if pool_size is None:
            return self._session_factory

        # 새 엔진 생성 (다른 pool_size)
        engine = create_async_engine(
            self._database_url,
            echo=False,
            future=True,
            pool_size=pool_size,
            max_overflow=self._max_overflow,
        )

        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """엔진 정리."""
        await self._engine.dispose()


# ============================================================
# Singleton & Helper Functions
# ============================================================

_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    SessionManager 싱글톤 인스턴스 반환.

    최초 호출 시 settings에서 DATABASE_URL을 읽어 생성.
    """
    global _session_manager
    if _session_manager is None:
        from app.core.config import settings

        _session_manager = SessionManager(
            database_url=settings.DATABASE_URL,
            pool_size=5,
            max_overflow=5,
        )
    return _session_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입용 세션.

    기존 db.py:get_session() 대체.
    """
    manager = get_session_manager()
    async with manager.session() as session:
        yield session


def create_worker_session_factory(num_workers: int) -> async_sessionmaker[AsyncSession]:
    """
    WorkerPool용 세션 팩토리 생성.

    기존 workers/pool.py:126-130의 패턴을 통합.

    Args:
        num_workers: 워커 수

    Returns:
        pool_size = num_workers + 2로 설정된 async_sessionmaker
    """
    manager = get_session_manager()
    return manager.create_session_factory(pool_size=num_workers + 2)


def _reset_session_manager() -> None:
    """
    테스트용 싱글톤 리셋.

    Warning: 프로덕션에서 사용하지 마세요.
    """
    global _session_manager
    _session_manager = None
