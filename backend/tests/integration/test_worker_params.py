"""
Test 5-Imp.34: Worker Parameter Integration Tests (RED Phase)
Expected to FAIL: Worker doesn't auto-extract URL parameters yet
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.asset import Asset
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskStatus, TaskType


@pytest.mark.asyncio
async def test_worker_auto_extracts_url_parameters(db_session: AsyncSession):
    """Test worker auto-extracts URL parameters during crawl - RED Phase"""
    # Setup
    project = Project(name="Worker Params Project")
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

    task = Task(
        project_id=project.id,
        target_id=target.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Mock CrawlerService to return URLs with query parameters
    urls_with_params = [
        "http://example.com/search?q=test&page=1",
        "http://example.com/filter?category=books&sort=recent",
    ]
    # http_data with parameters for each URL
    http_data = {
        "http://example.com/search?q=test&page=1": {
            "parameters": {"q": "test", "page": "1"}
        },
        "http://example.com/filter?category=books&sort=recent": {
            "parameters": {"category": "books", "sort": "recent"}
        },
    }

    # Mock crawler to return tuple (links, http_data, js_contents)
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(urls_with_params, http_data, [])
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify Assets have parameters field populated
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    # Should FAIL: Assets don't have parameters populated
    assert len(assets) == 2, "Should have created 2 assets"

    # Find asset with query parameters
    asset_with_params = next((a for a in assets if "search?q=test" in a.url), None)
    assert asset_with_params is not None, "Should find asset with query parameters"

    # Should FAIL: parameters field is None (not populated)
    assert asset_with_params.parameters is not None, "Asset should have parameters"
    assert "q" in asset_with_params.parameters, "Should have 'q' parameter"
    assert asset_with_params.parameters["q"] == "test"
    assert "page" in asset_with_params.parameters, "Should have 'page' parameter"
    assert asset_with_params.parameters["page"] == "1"


@pytest.mark.asyncio
async def test_worker_includes_parameters_in_asset_storage(db_session: AsyncSession):
    """Test parameters field included in Asset storage - RED Phase"""
    # Setup
    project = Project(name="Worker Asset Params Project")
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

    task = Task(
        project_id=project.id,
        target_id=target.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Mock crawler with URL containing multiple parameters
    url_with_many_params = (
        "http://example.com/api/users?status=active&role=admin&limit=50&offset=0"
    )
    # http_data with parameters
    http_data = {
        url_with_many_params: {
            "parameters": {
                "status": "active",
                "role": "admin",
                "limit": "50",
                "offset": "0",
            }
        }
    }

    # Mock crawler to return tuple (links, http_data, js_contents)
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=([url_with_many_params], http_data, [])
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify Asset has all parameters stored
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    assert len(assets) == 1
    asset = assets[0]

    # Should FAIL: parameters field is None
    assert asset.parameters is not None, "Asset should have parameters"
    assert len(asset.parameters) == 4, "Should have 4 parameters"
    assert asset.parameters["status"] == "active"
    assert asset.parameters["role"] == "admin"
    assert asset.parameters["limit"] == "50"
    assert asset.parameters["offset"] == "0"
