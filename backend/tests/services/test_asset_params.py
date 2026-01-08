"""
Test 5-Imp.33: AssetService Parameter Storage Tests (RED Phase)
Expected to FAIL: process_asset() doesn't accept parameters argument yet
"""
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.asset_service import AssetService
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType
from app.models.asset import AssetType, AssetSource


@pytest.mark.asyncio
async def test_asset_parameters_jsonb_storage(db_session: AsyncSession):
    """Test parameters JSONB field storage - RED Phase"""
    # Setup dependencies
    project = Project(name="Params Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Params Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Prepare parameters from URL query
    parameters = {
        "q": "search term",
        "page": "1",
        "limit": "20"
    }

    # Call process_asset with parameters
    # Should FAIL: TypeError - process_asset() got unexpected keyword argument 'parameters'
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/search?q=search+term&page=1&limit=20",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        parameters=parameters  # This parameter doesn't exist yet
    )

    # Verify parameters are stored in JSONB field
    assert asset.parameters is not None, "parameters should be stored"
    assert asset.parameters["q"] == "search term"
    assert asset.parameters["page"] == "1"
    assert asset.parameters["limit"] == "20"


@pytest.mark.asyncio
async def test_asset_parameters_null_allowed(db_session: AsyncSession):
    """Test NULL allowed when no query parameters - RED Phase"""
    # Setup
    project = Project(name="NULL Params Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Call process_asset WITHOUT parameters (URL has no query)
    # Should FAIL: process_asset signature doesn't have parameters parameter yet
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/about",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        parameters=None  # Explicitly None
    )

    # Verify NULL is allowed
    assert asset.parameters is None, "parameters should be None when URL has no query"


@pytest.mark.asyncio
async def test_asset_parameters_duplicate_merging(db_session: AsyncSession):
    """Test duplicate parameter merging into list - RED Phase"""
    # Setup
    project = Project(name="Duplicate Params Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(project_id=project.id, target_id=target.id, type=TaskType.CRAWL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    service = AssetService(db_session)

    # Prepare parameters with duplicate keys (multiple values)
    # This would come from: ?tag=python&tag=django&tag=web
    parameters = {
        "tag": ["python", "django", "web"],  # Multiple values as list
        "sort": "recent"
    }

    # Should FAIL: process_asset() doesn't accept parameters yet
    asset = await service.process_asset(
        target_id=target.id,
        task_id=task.id,
        url="http://example.com/posts?tag=python&tag=django&tag=web&sort=recent",
        method="GET",
        type=AssetType.URL,
        source=AssetSource.HTML,
        parameters=parameters
    )

    # Verify duplicate parameters are stored as list
    assert asset.parameters is not None
    assert "tag" in asset.parameters
    assert isinstance(asset.parameters["tag"], list), "Duplicate parameters should be list"
    assert len(asset.parameters["tag"]) == 3
    assert "python" in asset.parameters["tag"]
    assert "django" in asset.parameters["tag"]
    assert "web" in asset.parameters["tag"]
    assert asset.parameters["sort"] == "recent"
