"""
마이그레이션 CASCADE 제약 조건 테스트

Target 삭제 시 관련 데이터 자동 삭제를 위한 DB 외래 키 제약 조건 검증
"""

import pytest
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_tasks_target_id_cascade_constraint(db_session: AsyncSession):
    """tasks.target_id FK에 CASCADE가 설정되었는지 확인"""
    query = text(
        """
        SELECT delete_rule
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'tasks_target_id_fkey'
    """
    )
    result = await db_session.execute(query)
    row = result.fetchone()

    assert row is not None, "tasks.target_id FK constraint not found"
    assert (
        row.delete_rule == "CASCADE"
    ), f"tasks.target_id FK does not have CASCADE (current: {row.delete_rule})"


@pytest.mark.asyncio
async def test_assets_target_id_cascade_constraint(db_session: AsyncSession):
    """assets.target_id FK에 CASCADE가 설정되었는지 확인"""
    query = text(
        """
        SELECT delete_rule
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'assets_target_id_fkey'
    """
    )
    result = await db_session.execute(query)
    row = result.fetchone()

    assert row is not None, "assets.target_id FK constraint not found"
    assert (
        row.delete_rule == "CASCADE"
    ), f"assets.target_id FK does not have CASCADE (current: {row.delete_rule})"


@pytest.mark.asyncio
async def test_asset_discoveries_task_id_cascade_constraint(db_session: AsyncSession):
    """asset_discoveries.task_id FK에 CASCADE가 설정되었는지 확인"""
    query = text(
        """
        SELECT delete_rule
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'asset_discoveries_task_id_fkey'
    """
    )
    result = await db_session.execute(query)
    row = result.fetchone()

    assert row is not None, "asset_discoveries.task_id FK constraint not found"
    assert (
        row.delete_rule == "CASCADE"
    ), f"asset_discoveries.task_id FK does not have CASCADE (current: {row.delete_rule})"


@pytest.mark.asyncio
async def test_asset_discoveries_asset_id_cascade_constraint(db_session: AsyncSession):
    """asset_discoveries.asset_id FK에 CASCADE가 설정되었는지 확인"""
    query = text(
        """
        SELECT delete_rule
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'asset_discoveries_asset_id_fkey'
    """
    )
    result = await db_session.execute(query)
    row = result.fetchone()

    assert row is not None, "asset_discoveries.asset_id FK constraint not found"
    assert (
        row.delete_rule == "CASCADE"
    ), f"asset_discoveries.asset_id FK does not have CASCADE (current: {row.delete_rule})"


@pytest.mark.asyncio
async def test_asset_discoveries_parent_asset_id_cascade_constraint(
    db_session: AsyncSession,
):
    """asset_discoveries.parent_asset_id FK에 CASCADE가 설정되었는지 확인"""
    query = text(
        """
        SELECT delete_rule
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'asset_discoveries_parent_asset_id_fkey'
    """
    )
    result = await db_session.execute(query)
    row = result.fetchone()

    assert row is not None, "asset_discoveries.parent_asset_id FK constraint not found"
    assert (
        row.delete_rule == "CASCADE"
    ), f"asset_discoveries.parent_asset_id FK does not have CASCADE (current: {row.delete_rule})"
