"""
Test 5-Imp.2: Task Cancellation API Tests (RED Phase)
Expected to FAIL: 404 Not Found for /tasks/{id}/cancel endpoint
"""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.task import TaskStatus


@pytest.mark.asyncio
async def test_cancel_task_endpoint_exists(
    client: AsyncClient, db_session: AsyncSession
):
    """Test POST /tasks/{id}/cancel returns 200 OK - RED Phase"""
    # Setup: Create project, target, and trigger scan
    resp = await client.post("/api/v1/projects/", json={"name": "Cancel Test Proj"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Cancel Target", "url": "http://example.com"},
    )
    assert resp.status_code == 201
    target_id = resp.json()["id"]

    # Trigger scan to create a task
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    # Attempt to cancel task - should FAIL: 404 Not Found
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert resp.status_code == 200, "Cancel endpoint should return 200 OK"


@pytest.mark.asyncio
async def test_cancel_running_task_succeeds(
    client: AsyncClient, db_session: AsyncSession
):
    """Test cancelling a RUNNING task succeeds - RED Phase"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Running Cancel Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id = resp.json()["task_id"]

    # Manually update task to RUNNING status
    from app.models.task import Task
    from app.core.utils import utc_now
    from sqlmodel import select

    result = await db_session.exec(select(Task).where(Task.id == task_id))
    task = result.one()
    task.status = TaskStatus.RUNNING
    task.started_at = utc_now()
    await db_session.commit()

    # Cancel task - should FAIL: 404 Not Found
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert resp.status_code == 200

    # Verify task is now CANCELLED
    resp = await client.get(f"/api/v1/tasks/{task_id}")
    data = resp.json()
    assert data["status"] == "cancelled", "Task should be CANCELLED after cancellation"


@pytest.mark.asyncio
async def test_cancel_pending_task_succeeds(
    client: AsyncClient, db_session: AsyncSession
):
    """Test cancelling a PENDING task succeeds - RED Phase"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Pending Cancel Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id = resp.json()["task_id"]

    # Task is already PENDING, cancel immediately
    # should FAIL: 404 Not Found
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert resp.status_code == 200

    # Verify task is now CANCELLED
    resp = await client.get(f"/api/v1/tasks/{task_id}")
    data = resp.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_completed_task_fails(
    client: AsyncClient, db_session: AsyncSession
):
    """Test cancelling a COMPLETED task returns 400 Bad Request - RED Phase"""
    # Setup
    resp = await client.post(
        "/api/v1/projects/", json={"name": "Completed Cancel Proj"}
    )
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id = resp.json()["task_id"]

    # Manually update task to COMPLETED status
    from app.models.task import Task
    from app.core.utils import utc_now
    from sqlmodel import select

    result = await db_session.exec(select(Task).where(Task.id == task_id))
    task = result.one()
    task.status = TaskStatus.COMPLETED
    task.started_at = utc_now()
    task.completed_at = utc_now()
    await db_session.commit()

    # Attempt to cancel - should FAIL: 404 Not Found (endpoint doesn't exist)
    # But WHEN implemented, should return 400 Bad Request
    resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert resp.status_code == 400, "Cannot cancel a COMPLETED task"
