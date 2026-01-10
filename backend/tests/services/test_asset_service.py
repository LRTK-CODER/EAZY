import pytest
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.services.asset_service import AssetService
from app.models.task import Task
from app.models.asset import Asset, AssetDiscovery, AssetType, AssetSource

from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType

@pytest.mark.asyncio
async def test_create_asset_deduplication(db_session: AsyncSession):
    """
    Test that assets are deduplicated based on content_hash.
    """
    # 0. Setup Dependencies (Project -> Target -> Task)
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    
    target = Target(name="Test Target", project_id=project.id, url="http://example.com", scope=TargetScope.DOMAIN)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)
    
    task1 = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task1)
    await db_session.commit()
    await db_session.refresh(task1)
    
    task2 = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task2)
    await db_session.commit()
    await db_session.refresh(task2)

    # Mock data
    target_id = target.id
    task_id = task1.id
    method = "GET"
    url = "https://example.com/login"

    # Use Context Manager for batch processing
    async with AssetService(db_session) as service:
        # 1. First Discovery (New)
        asset1 = await service.process_asset(
            target_id=target_id,
            task_id=task_id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.HTML
        )

    # After context exit, assets are flushed
    await db_session.refresh(asset1)

    assert asset1.id is not None
    assert asset1.first_seen_at is not None
    first_seen = asset1.first_seen_at

    # Verify AssetDiscovery created
    result = await db_session.exec(select(AssetDiscovery).where(AssetDiscovery.asset_id == asset1.id))
    discoveries = result.all()
    assert len(discoveries) == 1
    assert discoveries[0].task_id == task_id

    # 2. Second Discovery (Duplicate) - Same content (method+url implied hash)
    # Different task_id to simulate a later scan
    task_id_2 = task2.id

    async with AssetService(db_session) as service:
        asset2 = await service.process_asset(
            target_id=target_id,
            task_id=task_id_2,
            url=url,
            method=method, # Same method + url -> Same hash
            type=AssetType.URL,
            source=AssetSource.HTML
        )

    # After context exit, assets are flushed
    await db_session.refresh(asset2)

    # Should stay the same record
    assert asset2.id == asset1.id
    assert asset2.last_seen_at >= asset1.last_seen_at
    assert asset2.first_seen_at == first_seen  # First seen should not change
    assert asset2.last_task_id == task_id_2

    # Verify NEW AssetDiscovery created
    result = await db_session.exec(select(AssetDiscovery).where(AssetDiscovery.asset_id == asset1.id))
    discoveries = result.all()
    assert len(discoveries) == 2
    task_ids = [d.task_id for d in discoveries]
    assert task_id in task_ids
    assert task_id_2 in task_ids
