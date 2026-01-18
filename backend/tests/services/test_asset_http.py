"""
Test 5-Imp.19: AssetService HTTP Storage Tests (RED Phase)
Expected to FAIL: process_asset() doesn't accept request_spec, response_spec parameters yet
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.asset import AssetSource, AssetType
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType
from app.services.asset_service import AssetService


@pytest.mark.asyncio
async def test_asset_request_spec_jsonb_storage(db_session: AsyncSession):
    """Test Asset.request_spec JSONB field storage - RED Phase"""
    # Setup dependencies
    project = Project(name="HTTP Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="HTTP Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Prepare HTTP request spec
    request_spec = {
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
        "body": None,
    }

    # Call process_asset with request_spec
    # Should FAIL: TypeError - process_asset() got unexpected keyword argument 'request_spec'
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/api/users",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        request_spec=request_spec,  # This parameter doesn't exist yet
    )

    # Verify request_spec is stored
    assert asset.request_spec is not None, "request_spec should be stored"
    assert asset.request_spec["method"] == "GET"
    assert "headers" in asset.request_spec


@pytest.mark.asyncio
async def test_asset_response_spec_jsonb_storage(db_session: AsyncSession):
    """Test Asset.response_spec JSONB field storage - RED Phase"""
    # Setup
    project = Project(name="HTTP Response Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Prepare HTTP response spec
    response_spec = {
        "status": 200,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-cache"},
        "body": '{"users": [{"id": 1, "name": "Alice"}]}',
    }

    # Call process_asset with response_spec
    # Should FAIL: TypeError - process_asset() got unexpected keyword argument 'response_spec'
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/api/users",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        response_spec=response_spec,  # This parameter doesn't exist yet
    )

    # Verify response_spec is stored
    assert asset.response_spec is not None, "response_spec should be stored"
    assert asset.response_spec["status"] == 200
    assert "body" in asset.response_spec


@pytest.mark.asyncio
async def test_asset_http_specs_null_allowed(db_session: AsyncSession):
    """Test NULL values allowed for HTTP specs - RED Phase"""
    # Setup
    project = Project(name="NULL Specs Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Call process_asset WITHOUT HTTP specs (should default to None)
    # Should FAIL: process_asset signature doesn't have these parameters yet
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/page",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        request_spec=None,
        response_spec=None,
    )

    # Verify NULL is allowed
    assert asset.request_spec is None, "request_spec should be None when not provided"
    assert asset.response_spec is None, "response_spec should be None when not provided"


@pytest.mark.asyncio
async def test_asset_http_body_truncation(db_session: AsyncSession):
    """Test truncation when body exceeds 10KB - RED Phase"""
    # Setup
    project = Project(name="Truncation Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Create large body (20KB)
    large_body = "x" * (20 * 1024)
    MAX_BODY_SIZE = 10 * 1024  # 10KB

    response_spec = {
        "status": 200,
        "headers": {"Content-Type": "text/html"},
        "body": large_body,
    }

    # Should FAIL: process_asset() doesn't accept response_spec yet
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/large",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        response_spec=response_spec,
    )

    # Verify body is truncated to 10KB
    assert asset.response_spec is not None
    stored_body = asset.response_spec.get("body", "")
    assert (
        len(stored_body) <= MAX_BODY_SIZE
    ), f"Body should be truncated to max {MAX_BODY_SIZE} bytes"
