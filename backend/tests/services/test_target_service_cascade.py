"""
Target 서비스 CASCADE 삭제 통합 테스트

Target 삭제 시 관련 Task, Asset, AssetDiscovery가 자동으로 삭제되는지 검증
"""

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.asset import Asset, AssetDiscovery, AssetSource, AssetType
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskStatus, TaskType
from app.services.target_service import TargetService


@pytest.mark.asyncio
async def test_delete_target_cascades_tasks(db_session: AsyncSession):
    """Target 삭제 시 관련 Task가 CASCADE로 삭제되는지 검증"""
    # 1. Project 생성
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 2. Target 생성
    target = Target(
        project_id=project.id,
        name="Test Target",
        url="https://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    # 3. Task 생성 (Target에 연결)
    task = Task(
        project_id=project.id,
        target_id=target.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 4. Task가 생성되었는지 확인
    query = select(Task).where(Task.target_id == target.id)
    result = await db_session.exec(query)
    tasks_before = result.all()
    assert len(tasks_before) == 1, "Task should exist before target deletion"

    # 5. Target 삭제
    target_service = TargetService(db_session)
    delete_result = await target_service.delete_target(target.id)
    assert delete_result is True, "Target deletion should succeed"

    # 6. Task가 CASCADE로 삭제되었는지 확인
    query = select(Task).where(Task.id == task.id)
    result = await db_session.exec(query)
    tasks_after = result.all()
    assert len(tasks_after) == 0, "Task should be CASCADE deleted with target"


@pytest.mark.asyncio
async def test_delete_target_cascades_assets(db_session: AsyncSession):
    """Target 삭제 시 관련 Asset이 CASCADE로 삭제되는지 검증"""
    # 1. Project, Target 생성
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        project_id=project.id,
        name="Test Target",
        url="https://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    # 2. Asset 생성 (Target에 연결)
    asset = Asset(
        target_id=target.id,
        content_hash="abc123hash",
        type=AssetType.URL,
        source=AssetSource.HTML,
        method="GET",
        url="https://example.com/page1",
        path="/page1",
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    # 3. Asset이 생성되었는지 확인
    query = select(Asset).where(Asset.target_id == target.id)
    result = await db_session.exec(query)
    assets_before = result.all()
    assert len(assets_before) == 1, "Asset should exist before target deletion"

    # 4. Target 삭제
    target_service = TargetService(db_session)
    delete_result = await target_service.delete_target(target.id)
    assert delete_result is True, "Target deletion should succeed"

    # 5. Asset이 CASCADE로 삭제되었는지 확인
    query = select(Asset).where(Asset.id == asset.id)
    result = await db_session.exec(query)
    assets_after = result.all()
    assert len(assets_after) == 0, "Asset should be CASCADE deleted with target"


@pytest.mark.asyncio
async def test_delete_target_cascades_asset_discoveries(db_session: AsyncSession):
    """Target 삭제 시 AssetDiscovery도 CASCADE로 삭제되는지 검증"""
    # 1. Project, Target 생성
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        project_id=project.id,
        name="Test Target",
        url="https://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    # 2. Task 생성
    task = Task(
        project_id=project.id,
        target_id=target.id,
        type=TaskType.CRAWL,
        status=TaskStatus.COMPLETED,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 3. Asset 생성
    asset = Asset(
        target_id=target.id,
        content_hash="xyz789hash",
        type=AssetType.URL,
        source=AssetSource.HTML,
        method="GET",
        url="https://example.com/page2",
        path="/page2",
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    # 4. AssetDiscovery 생성 (Task와 Asset 연결)
    discovery = AssetDiscovery(task_id=task.id, asset_id=asset.id, parent_asset_id=None)
    db_session.add(discovery)
    await db_session.commit()
    await db_session.refresh(discovery)

    # 5. AssetDiscovery가 생성되었는지 확인
    query = select(AssetDiscovery).where(AssetDiscovery.asset_id == asset.id)
    result = await db_session.exec(query)
    discoveries_before = result.all()
    assert (
        len(discoveries_before) == 1
    ), "AssetDiscovery should exist before target deletion"

    # 6. Target 삭제
    target_service = TargetService(db_session)
    delete_result = await target_service.delete_target(target.id)
    assert delete_result is True, "Target deletion should succeed"

    # 7. AssetDiscovery가 CASCADE로 삭제되었는지 확인
    # (Target 삭제 → Asset 삭제 → AssetDiscovery 삭제 체인)
    query = select(AssetDiscovery).where(AssetDiscovery.id == discovery.id)
    result = await db_session.exec(query)
    discoveries_after = result.all()
    assert (
        len(discoveries_after) == 0
    ), "AssetDiscovery should be CASCADE deleted (via Asset)"


@pytest.mark.asyncio
async def test_delete_target_with_multiple_relations(db_session: AsyncSession):
    """Target 삭제 시 여러 Task와 Asset이 모두 CASCADE 삭제되는지 검증"""
    # 1. Project, Target 생성
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        project_id=project.id,
        name="Test Target",
        url="https://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    # 2. 여러 Task 생성 (3개)
    tasks = []
    for i in range(3):
        task = Task(
            project_id=project.id,
            target_id=target.id,
            type=TaskType.CRAWL,
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        tasks.append(task)
    await db_session.commit()

    # 3. 여러 Asset 생성 (5개)
    assets = []
    for i in range(5):
        asset = Asset(
            target_id=target.id,
            content_hash=f"hash{i}",
            type=AssetType.URL,
            source=AssetSource.HTML,
            method="GET",
            url=f"https://example.com/page{i}",
            path=f"/page{i}",
        )
        db_session.add(asset)
        assets.append(asset)
    await db_session.commit()

    # 4. 데이터 존재 확인
    query_tasks = select(Task).where(Task.target_id == target.id)
    result = await db_session.exec(query_tasks)
    assert len(result.all()) == 3, "Should have 3 tasks"

    query_assets = select(Asset).where(Asset.target_id == target.id)
    result = await db_session.exec(query_assets)
    assert len(result.all()) == 5, "Should have 5 assets"

    # 5. Target 삭제
    target_service = TargetService(db_session)
    delete_result = await target_service.delete_target(target.id)
    assert delete_result is True

    # 6. 모든 Task와 Asset이 삭제되었는지 확인
    query_tasks = select(Task).where(Task.target_id == target.id)
    result = await db_session.exec(query_tasks)
    assert len(result.all()) == 0, "All tasks should be CASCADE deleted"

    query_assets = select(Asset).where(Asset.target_id == target.id)
    result = await db_session.exec(query_assets)
    assert len(result.all()) == 0, "All assets should be CASCADE deleted"
