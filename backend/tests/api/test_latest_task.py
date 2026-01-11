"""
Test 5-Imp.3: Latest Task API Tests (RED Phase)
Expected to FAIL: 404 Not Found for /targets/{id}/latest-task endpoint
"""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_get_latest_task_endpoint_exists(
    client: AsyncClient, db_session: AsyncSession
):
    """Test GET /targets/{id}/latest-task returns 200 OK - RED Phase"""
    # Setup: Create project and target
    resp = await client.post("/api/v1/projects/", json={"name": "Latest Task Proj"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "http://example.com"},
    )
    assert resp.status_code == 201
    target_id = resp.json()["id"]

    # Trigger scan to create a task
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    # Get latest task - should FAIL: 404 Not Found
    resp = await client.get(f"/api/v1/targets/{target_id}/latest-task")
    assert resp.status_code == 200, "Latest task endpoint should return 200 OK"

    # Verify it returns the task we just created
    data = resp.json()
    assert data["id"] == task_id


@pytest.mark.asyncio
async def test_get_latest_task_returns_most_recent(
    client: AsyncClient, db_session: AsyncSession
):
    """Test returns most recent task (ORDER BY created_at DESC) - RED Phase"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Recent Task Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]

    # Trigger multiple scans
    resp1 = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id_1 = resp1.json()["task_id"]

    resp2 = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id_2 = resp2.json()["task_id"]

    resp3 = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id_3 = resp3.json()["task_id"]

    # Get latest task - should FAIL: 404 Not Found
    resp = await client.get(f"/api/v1/targets/{target_id}/latest-task")
    assert resp.status_code == 200

    # Verify it returns the LAST created task (task_id_3)
    data = resp.json()
    assert data["id"] == task_id_3, "Should return most recent task"
    assert data["id"] != task_id_1, "Should not return oldest task"
    assert data["id"] != task_id_2, "Should not return middle task"


@pytest.mark.asyncio
async def test_get_latest_task_returns_404_when_no_tasks(
    client: AsyncClient, db_session: AsyncSession
):
    """Test returns 404 when target has no tasks - RED Phase"""
    # Setup: Create project and target, but NO scans
    resp = await client.post("/api/v1/projects/", json={"name": "No Tasks Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target No Scans", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]

    # Get latest task - should FAIL: 404 Not Found (endpoint doesn't exist)
    # But WHEN implemented with no tasks, should ALSO return 404
    resp = await client.get(f"/api/v1/targets/{target_id}/latest-task")
    assert resp.status_code == 404, "Should return 404 when target has no tasks"

    # Verify error message
    data = resp.json()
    assert "detail" in data
    assert "no tasks" in data["detail"].lower() or "not found" in data["detail"].lower()
