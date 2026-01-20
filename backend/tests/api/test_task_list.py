"""Tests for GET /targets/{target_id}/tasks endpoint."""

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.utils import utc_now
from app.models.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_get_tasks_for_target_returns_list(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /targets/{id}/tasks -> Task 목록 반환"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Task List Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "https://example.com"},
    )
    target_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id = resp.json()["task_id"]

    # Act
    resp = await client.get(f"/api/v1/targets/{target_id}/tasks")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == task_id


@pytest.mark.asyncio
async def test_get_tasks_for_target_sorted_by_created_at_desc(
    client: AsyncClient, db_session: AsyncSession
):
    """최신 Task가 먼저 반환 (ORDER BY created_at DESC)"""
    # Setup: 3개 Task 생성
    resp = await client.post("/api/v1/projects/", json={"name": "Sort Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "https://example.com"},
    )
    target_id = resp.json()["id"]

    task_ids = []
    for _ in range(3):
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        task_id = resp.json()["task_id"]
        task_ids.append(task_id)

        # Complete task to allow next scan
        result = await db_session.exec(select(Task).where(Task.id == task_id))
        task = result.one()
        task.status = TaskStatus.COMPLETED
        task.completed_at = utc_now()
        await db_session.commit()

    # Act
    resp = await client.get(f"/api/v1/targets/{target_id}/tasks")
    data = resp.json()

    # Assert: 최신 Task가 먼저
    assert data[0]["id"] == task_ids[-1]
    assert data[-1]["id"] == task_ids[0]


@pytest.mark.asyncio
async def test_get_tasks_for_target_with_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """skip=2&limit=2 -> 2개 Task 반환"""
    # Setup: 5개 Task 생성
    resp = await client.post("/api/v1/projects/", json={"name": "Page Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "https://example.com"},
    )
    target_id = resp.json()["id"]

    for _ in range(5):
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        task_id = resp.json()["task_id"]

        result = await db_session.exec(select(Task).where(Task.id == task_id))
        task = result.one()
        task.status = TaskStatus.COMPLETED
        task.completed_at = utc_now()
        await db_session.commit()

    # Act
    resp = await client.get(f"/api/v1/targets/{target_id}/tasks?skip=2&limit=2")
    data = resp.json()

    # Assert
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_tasks_for_target_with_status_filter(
    client: AsyncClient, db_session: AsyncSession
):
    """status=completed -> 완료된 Task만 반환"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Filter Proj"})
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target", "url": "https://example.com"},
    )
    target_id = resp.json()["id"]

    # Create 2 tasks: 1 completed, 1 pending
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task1_id = resp.json()["task_id"]

    result = await db_session.exec(select(Task).where(Task.id == task1_id))
    task1 = result.one()
    task1.status = TaskStatus.COMPLETED
    task1.completed_at = utc_now()
    await db_session.commit()

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    # task2 remains PENDING

    # Act
    resp = await client.get(f"/api/v1/targets/{target_id}/tasks?status=completed")
    data = resp.json()

    # Assert
    assert len(data) == 1
    assert all(t["status"] == "completed" for t in data)
