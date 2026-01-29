"""SessionManager 단위 테스트."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class TestSessionManager:
    """SessionManager 클래스 테스트."""

    @pytest.mark.asyncio
    async def test_session_commits_on_success(self):
        """성공 시 자동 커밋."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine"):
            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test"
            )

        mock_session = AsyncMock(spec=AsyncSession)
        manager._session_factory = MagicMock(return_value=mock_session)

        async with manager.session():
            pass  # 정상 종료

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_rollbacks_on_exception(self):
        """예외 시 자동 롤백."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine"):
            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test"
            )

        mock_session = AsyncMock(spec=AsyncSession)
        manager._session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(ValueError):
            async with manager.session():
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_closes_after_use(self):
        """사용 후 세션 닫힘."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine"):
            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test"
            )

        mock_session = AsyncMock(spec=AsyncSession)
        manager._session_factory = MagicMock(return_value=mock_session)

        async with manager.session():
            pass

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_nested_transaction_with_savepoint(self):
        """SAVEPOINT를 사용한 중첩 트랜잭션."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine"):
            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test"
            )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_nested = AsyncMock()
        mock_nested.__aenter__ = AsyncMock(return_value=mock_nested)
        mock_nested.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin_nested = MagicMock(return_value=mock_nested)

        manager._session_factory = MagicMock(return_value=mock_session)

        async with manager.session() as session:
            async with manager.transaction(session):
                pass  # 중첩 트랜잭션

        mock_session.begin_nested.assert_called_once()

    def test_connection_pool_configuration(self):
        """Connection pool 설정 적용."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine"):
            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test",
                pool_size=10,
                max_overflow=5,
            )

        assert manager.pool_size == 10
        assert manager.max_overflow == 5

    def test_engine_created_with_correct_params(self):
        """엔진이 올바른 파라미터로 생성됨."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine

            SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test",
                pool_size=6,
                max_overflow=5,
            )

            mock_create_engine.assert_called_once()
            call_kwargs = mock_create_engine.call_args[1]
            assert call_kwargs["pool_size"] == 6
            assert call_kwargs["max_overflow"] == 5


class TestSessionManagerSingleton:
    """싱글톤 및 팩토리 함수 테스트."""

    def test_get_session_manager_returns_singleton(self):
        """get_session_manager()는 싱글톤 인스턴스 반환."""
        from app.core.session import _reset_session_manager, get_session_manager

        _reset_session_manager()  # 테스트 격리

        with patch("app.core.session.create_async_engine"):
            manager1 = get_session_manager()
            manager2 = get_session_manager()

        assert manager1 is manager2

        _reset_session_manager()  # 정리

    @pytest.mark.asyncio
    async def test_get_session_yields_session(self):
        """get_session()은 세션을 yield."""
        from contextlib import asynccontextmanager

        from app.core.session import _reset_session_manager, get_session

        _reset_session_manager()

        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.session.get_session_manager") as mock_get_manager:
            mock_manager = MagicMock()

            # session() 메서드가 async context manager를 반환하도록 설정
            @asynccontextmanager
            async def fake_session():
                yield mock_session

            mock_manager.session = fake_session
            mock_get_manager.return_value = mock_manager

            async for session in get_session():
                assert session is mock_session
                break

    def test_create_worker_session_factory(self):
        """create_worker_session_factory()는 async_sessionmaker 반환."""
        from app.core.session import (
            _reset_session_manager,
            create_worker_session_factory,
        )

        _reset_session_manager()

        with patch("app.core.session.get_session_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_factory = MagicMock(spec=async_sessionmaker)
            mock_manager.create_session_factory.return_value = mock_factory
            mock_get_manager.return_value = mock_manager

            create_worker_session_factory(num_workers=4)

            mock_manager.create_session_factory.assert_called_once_with(
                pool_size=6
            )  # 4+2


class TestSessionManagerCleanup:
    """리소스 정리 테스트."""

    @pytest.mark.asyncio
    async def test_dispose_closes_engine(self):
        """dispose()는 엔진을 닫음."""
        from app.core.session import SessionManager

        with patch("app.core.session.create_async_engine") as mock_create_engine:
            mock_engine = AsyncMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine

            manager = SessionManager(
                database_url="postgresql+asyncpg://test:test@localhost/test"
            )

            await manager.dispose()

            mock_engine.dispose.assert_called_once()
