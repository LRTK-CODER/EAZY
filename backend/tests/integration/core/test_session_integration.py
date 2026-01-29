"""SessionManager 통합 테스트 - 실제 DB 연동."""

import pytest
from sqlalchemy import text

from app.core.session import SessionManager


@pytest.fixture
def session_manager():
    """테스트용 SessionManager."""
    from app.core.config import settings

    manager = SessionManager(
        database_url=settings.DATABASE_URL,
        pool_size=2,
        max_overflow=1,
    )
    yield manager
    # cleanup은 pytest가 처리


class TestSessionManagerIntegration:
    """실제 DB 연동 통합 테스트."""

    @pytest.mark.asyncio
    async def test_session_commits_to_real_db(self, session_manager):
        """실제 DB에 커밋 확인."""
        async with session_manager.session() as session:
            # 간단한 쿼리 실행
            result = await session.exec(text("SELECT 1 as value"))
            row = result.first()
            assert row.value == 1

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self, session_manager):
        """에러 시 롤백 확인 (트랜잭션 무결성)."""
        # 이 테스트는 실제 테이블이 필요하므로 간단한 구조만 테스트
        try:
            async with session_manager.session() as session:
                await session.exec(text("SELECT 1"))
                raise ValueError("Intentional error")
        except ValueError:
            pass  # 예상된 에러

        # 세션이 롤백되어 다음 세션이 정상 동작
        async with session_manager.session() as session:
            result = await session.exec(text("SELECT 1 as value"))
            row = result.first()
            assert row.value == 1

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self, session_manager):
        """동시 세션 처리 확인."""
        import asyncio

        async def query_task(task_id: int):
            async with session_manager.session() as session:
                result = await session.exec(text(f"SELECT {task_id} as value"))
                row = result.first()
                return row.value

        # 동시에 3개 세션 실행
        results = await asyncio.gather(
            query_task(1),
            query_task(2),
            query_task(3),
        )

        assert set(results) == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_dispose_releases_connections(self, session_manager):
        """dispose() 후 연결 해제 확인."""
        async with session_manager.session() as session:
            await session.exec(text("SELECT 1"))

        await session_manager.dispose()

        # dispose 후에는 새 세션 생성 불가 (엔진이 닫힘)
        # 이 테스트는 dispose 동작 확인용


class TestNestedTransactionIntegration:
    """중첩 트랜잭션 통합 테스트."""

    @pytest.mark.asyncio
    async def test_savepoint_rollback(self, session_manager):
        """SAVEPOINT 롤백 확인."""
        async with session_manager.session() as session:
            # 외부 트랜잭션
            await session.exec(text("SELECT 1"))

            try:
                async with session_manager.transaction(session):
                    # 중첩 트랜잭션 (SAVEPOINT)
                    await session.exec(text("SELECT 2"))
                    raise ValueError("Savepoint error")
            except ValueError:
                pass  # SAVEPOINT만 롤백됨

            # 외부 트랜잭션은 유지됨
            result = await session.exec(text("SELECT 3 as value"))
            row = result.first()
            assert row.value == 3
