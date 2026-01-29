import asyncio

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.asset import Asset, AssetDiscovery, AssetSource, AssetType
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType
from app.services.asset_service import AssetService


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

    target = Target(
        name="Test Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
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
            source=AssetSource.HTML,
        )

    # After context exit, assets are flushed
    # Re-query the asset since upsert doesn't track the object in session
    assert asset1.id is not None
    result = await db_session.exec(select(Asset).where(Asset.id == asset1.id))
    asset1 = result.one()

    assert asset1.first_seen_at is not None
    first_seen = asset1.first_seen_at

    # Verify AssetDiscovery created
    result = await db_session.exec(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == asset1.id)
    )
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
            method=method,  # Same method + url -> Same hash
            type=AssetType.URL,
            source=AssetSource.HTML,
        )

    # After context exit, assets are flushed
    # Re-query the asset since upsert doesn't track the object in session
    result = await db_session.exec(select(Asset).where(Asset.id == asset2.id))
    asset2 = result.one()

    # Should stay the same record
    assert asset2.id == asset1.id
    assert asset2.last_seen_at >= asset1.last_seen_at
    assert asset2.first_seen_at == first_seen  # First seen should not change
    assert asset2.last_task_id == task_id_2

    # Verify NEW AssetDiscovery created
    result = await db_session.exec(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == asset1.id)
    )
    discoveries = result.all()
    assert len(discoveries) == 2
    task_ids = [d.task_id for d in discoveries]
    assert task_id in task_ids
    assert task_id_2 in task_ids


@pytest.mark.asyncio
async def test_process_asset_deduplication_from_db_same_session(
    db_session: AsyncSession,
):
    """
    Test that processing the same DB-loaded asset multiple times within one session
    does NOT cause StaleDataError.

    Regression test for: UPDATE statement on table 'assets' expected to update 1 row(s); 0 were matched.

    This tests the fix where DB-loaded assets are added to _pending_hash_map
    to prevent duplicate SELECT queries returning different object instances
    for the same DB row.
    """
    # Setup: Project -> Target -> Task
    project = Project(name="Dedup Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Dedup Test Target",
        project_id=project.id,
        url="http://dedup-test.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    url = "https://dedup-test.com/api/endpoint"
    method = "GET"

    # Step 1: Create the asset in a separate session context (simulate previous scan)
    async with AssetService(db_session) as service:
        initial_asset = await service.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,
        )
    # Re-query the asset since upsert doesn't track the object in session
    initial_id = initial_asset.id
    result = await db_session.exec(select(Asset).where(Asset.id == initial_id))
    initial_asset = result.one()

    # Step 2: Process the SAME asset MULTIPLE times in a single session
    # This simulates the real-world scenario where the same URL is discovered
    # multiple times during crawling (e.g., linked from multiple pages)
    async with AssetService(db_session) as service:
        # First processing - loads from DB
        asset1 = await service.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,
        )

        # Second processing - should use cached version from _pending_hash_map
        asset2 = await service.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,
        )

        # Third processing - should still use cached version
        asset3 = await service.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,
        )

        # All should be the SAME object instance (identity check)
        assert asset1 is asset2, "asset1 and asset2 should be the same instance"
        assert asset2 is asset3, "asset2 and asset3 should be the same instance"

    # flush() completed without StaleDataError - test passes
    # The asset should still have the same ID
    # Re-query the asset since upsert doesn't track the object in session
    result = await db_session.exec(select(Asset).where(Asset.id == asset1.id))
    asset1_reloaded = result.one()
    assert asset1_reloaded.id == initial_id, "Asset ID should not change"

    # Verify 4 discoveries created (1 initial + 3 in second session)
    result = await db_session.exec(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == initial_id)
    )
    discoveries = result.all()
    assert len(discoveries) == 4, f"Expected 4 discoveries, got {len(discoveries)}"


@pytest.mark.asyncio
async def test_upsert_handles_race_condition(db_session: AsyncSession):
    """
    Test that upsert (ON CONFLICT DO UPDATE) handles race conditions where
    two workers try to insert the same content_hash simultaneously.

    Regression test for: duplicate key value violates unique constraint "ix_assets_content_hash"

    This tests the fix where we use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
    instead of session.add_all() to handle concurrent inserts.
    """
    # Setup: Project -> Target -> Task
    project = Project(name="Race Condition Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Race Condition Test Target",
        project_id=project.id,
        url="http://race-test.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    url = "https://race-test.com/api/endpoint"
    method = "GET"

    # Simulate the race condition scenario:
    # Two workers process the same URL simultaneously, but with different timestamps
    # Previously this would cause: UniqueViolationError on content_hash

    # First service creates and flushes an asset
    async with AssetService(db_session) as service1:
        asset1 = await service1.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.HTML,
        )

    # Second service creates an asset with the SAME content_hash (method+url)
    # but different timestamps (simulating a parallel worker)
    async with AssetService(db_session) as service2:
        asset2 = await service2.process_asset(
            target_id=target.id,
            task_id=task.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,  # Different source
        )

    # Both should complete without IntegrityError
    assert asset1.id is not None, "asset1 should have an ID"
    assert asset2.id is not None, "asset2 should have an ID"

    # Re-query to verify the asset exists
    result = await db_session.exec(select(Asset).where(Asset.id == asset1.id))
    asset = result.one()
    assert asset is not None
    assert asset.content_hash is not None

    # Verify only ONE asset exists with this content_hash
    result = await db_session.exec(
        select(Asset).where(Asset.content_hash == asset.content_hash)
    )
    assets = result.all()
    assert len(assets) == 1, f"Expected 1 asset, got {len(assets)}"


@pytest.mark.asyncio
async def test_upsert_updates_fields_on_conflict(db_session: AsyncSession):
    """
    Test that upsert properly updates last_seen_at, last_task_id, and spec fields
    when a conflict occurs (same content_hash).
    """
    # Setup: Project -> Target -> Tasks
    project = Project(name="Upsert Update Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Upsert Update Target",
        project_id=project.id,
        url="http://upsert-update.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task1 = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    task2 = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add_all([task1, task2])
    await db_session.commit()
    await db_session.refresh(task1)
    await db_session.refresh(task2)

    url = "https://upsert-update.com/api/test"
    method = "POST"

    # First insert with initial request_spec
    async with AssetService(db_session) as service:
        asset1 = await service.process_asset(
            target_id=target.id,
            task_id=task1.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.HTML,
            request_spec={"method": "POST", "body": "initial_body"},
        )

    asset1_id = asset1.id
    result = await db_session.exec(select(Asset).where(Asset.id == asset1_id))
    asset_initial = result.one()
    first_seen = asset_initial.first_seen_at

    # Simulate time passing
    await asyncio.sleep(0.01)

    # Second insert (upsert) with updated request_spec and different task_id
    async with AssetService(db_session) as service:
        asset2 = await service.process_asset(
            target_id=target.id,
            task_id=task2.id,
            url=url,
            method=method,
            type=AssetType.URL,
            source=AssetSource.NETWORK,
            request_spec={"method": "POST", "body": "updated_body"},
        )

    # Re-query the asset
    result = await db_session.exec(select(Asset).where(Asset.id == asset1_id))
    asset_updated = result.one()

    # Verify:
    # 1. ID is the same (upsert, not new insert)
    assert asset2.id == asset1_id

    # 2. first_seen_at is preserved (not updated)
    assert asset_updated.first_seen_at == first_seen

    # 3. last_seen_at is updated
    assert asset_updated.last_seen_at >= first_seen

    # 4. last_task_id is updated
    assert asset_updated.last_task_id == task2.id

    # 5. request_spec is updated
    assert asset_updated.request_spec == {"method": "POST", "body": "updated_body"}
