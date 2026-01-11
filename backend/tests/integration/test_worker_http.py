"""
Test 5-Imp.20: Worker HTTP Integration Tests (GREEN Phase)
Expected to PASS: Worker collects and passes HTTP data with Base64 image encoding
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType, TaskStatus
from app.models.asset import Asset
from sqlmodel import select
import base64


@pytest.mark.asyncio
async def test_worker_collects_http_data_during_crawl(db_session: AsyncSession):
    """Test worker collects HTTP data during crawling - RED Phase"""
    # Setup
    project = Project(name="Worker HTTP Project")
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

    # Mock CrawlerService to return HTTP data
    mock_http_data = {
        "http://example.com/page": {
            "request": {"method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
            "response": {
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "body": "<html>...</html>",
            },
        }
    }

    # Should FAIL: CrawlerService.crawl() returns List[str], not tuple
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        # Current signature: returns List[str]
        # Expected new signature: returns Tuple[List[str], Dict]
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(["http://example.com/page"], mock_http_data)
        )

        # Import and call worker function
        from app.worker import process_task

        # Should FAIL: process_task doesn't handle tuple return yet
        await process_task(task.id, db_session)

    # Verify task completed
    await db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_worker_passes_http_data_to_asset_service(db_session: AsyncSession):
    """Test HTTP data passed to AssetService - RED Phase"""
    # Setup
    project = Project(name="Worker Asset HTTP Project")
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

    # Mock HTTP data
    mock_http_data = {
        "http://example.com/api": {
            "request": {"method": "GET", "headers": {}},
            "response": {"status": 200, "body": '{"success": true}'},
        }
    }

    # Should FAIL: Worker doesn't extract and pass HTTP data to AssetService
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(["http://example.com/api"], mock_http_data)
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify Asset has HTTP data
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    # Should FAIL: Assets don't have request_spec/response_spec populated
    assert len(assets) > 0, "Should have created assets"
    asset = assets[0]
    assert asset.request_spec is not None, "Asset should have request_spec"
    assert asset.response_spec is not None, "Asset should have response_spec"


@pytest.mark.asyncio
async def test_worker_parses_json_response_bodies(db_session: AsyncSession):
    """Test API response body JSON parsing - RED Phase"""
    # Setup
    project = Project(name="JSON Parsing Project")
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

    # Mock JSON API response
    json_body = '{"users": [{"id": 1, "name": "Alice"}]}'
    mock_http_data = {
        "http://example.com/api/users": {
            "request": {"method": "GET"},
            "response": {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json_body,
            },
        }
    }

    # Should FAIL: Worker doesn't handle HTTP data
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(["http://example.com/api/users"], mock_http_data)
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify JSON body is stored
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    assert len(assets) > 0
    asset = assets[0]
    assert asset.response_spec is not None
    assert "body" in asset.response_spec
    assert "users" in asset.response_spec["body"]  # JSON content preserved


@pytest.mark.asyncio
async def test_worker_excludes_image_responses(db_session: AsyncSession):
    """Test image responses encoded as Base64 (Content-Type: image/*) - GREEN Phase"""
    # Setup
    project = Project(name="Image Exclusion Project")
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

    # Mock image response (Base64 encoded as CrawlerService does)
    image_bytes = b"binary image data..."
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    mock_http_data = {
        "http://example.com/logo.png": {
            "request": {"method": "GET"},
            "response": {
                "status": 200,
                "headers": {"Content-Type": "image/png"},
                "body": image_base64,  # Base64 encoded string
            },
        }
    }

    # Should PASS: Worker encodes image responses as Base64
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(["http://example.com/logo.png"], mock_http_data)
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify image response body is Base64 encoded
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    assert len(assets) > 0, "Should have created asset for image"
    asset = assets[0]
    assert asset.response_spec is not None, "Asset should have response_spec"
    assert "body" in asset.response_spec, "Response should have body"

    # Image body should be Base64 encoded string
    body = asset.response_spec["body"]
    assert isinstance(body, str), "Image body should be Base64 string"
    assert body == image_base64, "Image body should match Base64 encoding"


@pytest.mark.asyncio
async def test_full_integration_worker_crawler_asset(db_session: AsyncSession):
    """Test full integration: Worker → CrawlerService → AssetService - RED Phase"""
    # Setup
    project = Project(name="Full Integration Project")
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

    # Mock complete HTTP data flow
    mock_http_data = {
        "http://example.com/about": {
            "request": {"method": "GET", "headers": {"User-Agent": "EAZY/1.0"}},
            "response": {
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "body": "<html><body>About Us</body></html>",
            },
        }
    }

    # Should FAIL: End-to-end HTTP data flow not implemented
    with patch("app.worker.CrawlerService") as MockCrawler:
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.crawl = AsyncMock(
            return_value=(["http://example.com/about"], mock_http_data)
        )

        from app.worker import process_task

        await process_task(task.id, db_session)

    # Verify complete flow
    await db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED

    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()

    assert len(assets) == 1
    asset = assets[0]

    # Verify HTTP data is persisted
    assert asset.request_spec is not None, "request_spec should be stored"
    assert asset.request_spec["method"] == "GET"
    assert asset.response_spec is not None, "response_spec should be stored"
    assert asset.response_spec["status"] == 200
    assert "body" in asset.response_spec
