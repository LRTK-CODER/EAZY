import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.queue import TaskManager
from app.models.task import TaskStatus
from app.worker import process_one_task


@pytest.mark.asyncio
async def test_full_scan_flow(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """
    Integration Test: Full Scan Flow
    1. Create Project
    2. Create Target
    3. Trigger Scan (API) -> Enqueue to Redis
    4. Worker picks up Task (Manual Trigger of worker function)
    5. Verify Task Status is COMPLETED
    6. Verify Assets are created
    """

    # 1. Create Project
    resp = await client.post("/api/v1/projects/", json={"name": "Integration Proj"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # 2. Create Target
    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Integration Target", "url": "http://example.com"},
    )
    assert resp.status_code == 201
    target_id = resp.json()["id"]

    # 3. Trigger Scan
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    # Verify Pending
    resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert resp.json()["status"] == TaskStatus.PENDING

    # 4. Run Worker (Simulate Background Process)
    # The queue should have the task now.
    task_manager = TaskManager(redis_client)

    # We must patch the crawler to avoid real network calls, consistent with unit tests
    from unittest.mock import patch

    with patch("app.services.crawler_service.CrawlerService.crawl") as mock_crawl:
        # Return tuple (links, http_data) as per crawler interface
        mock_crawl.return_value = (
            ["http://example.com/page1", "http://example.com/page2"],
            {},  # Empty http_data
        )

        # Process the task
        await process_one_task(db_session, task_manager)

    # 5. Verify Completed
    resp = await client.get(f"/api/v1/tasks/{task_id}")
    data = resp.json()
    assert data["status"] == TaskStatus.COMPLETED

    # 6. Verify Assets
    resp = await client.get(f"/api/v1/tasks/{task_id}/assets")
    assets = resp.json()
    assert len(assets) == 2
    urls = [a["url"] for a in assets]
    assert "http://example.com/page1" in urls
