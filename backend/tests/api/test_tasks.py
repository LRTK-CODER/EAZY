import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.task import TaskStatus


@pytest.mark.asyncio
async def test_trigger_scan_task(client: AsyncClient, db_session: AsyncSession):
    """
    Test triggering a scan task via API.
    POST /projects/{id}/targets/{id}/scan
    """
    # 1. Setup Data
    resp = await client.post("/api/v1/projects/", json={"name": "Scan Proj"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Scan Target", "url": "http://example.com"},
    )
    assert resp.status_code == 201
    target_id = resp.json()["id"]

    # 2. Trigger Scan
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")

    if resp.status_code != 202:
        print(f"Error Response: {resp.text}")
    assert resp.status_code == 202
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    return data["task_id"]


@pytest.mark.asyncio
async def test_get_task_status(client: AsyncClient, db_session: AsyncSession):
    """
    Test retrieving task status.
    GET /tasks/{id}
    """
    # 1. Reuse trigger logic or setup new
    # For speed, let's just trigger a new one
    resp = await client.post("/api/v1/projects/", json={"name": "Status Proj"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]
    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target Status", "url": "http://example.com"},
    )
    assert resp.status_code == 201
    target_id = resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    if resp.status_code != 202:
        print(
            f"DEBUG: Scan trigger failed. Status: {resp.status_code}, Body: {resp.text}"
        )
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    # 2. Get Status
    resp = await client.get(f"/api/v1/tasks/{task_id}")

    # EXPECT FAIL (404) until implemented
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == task_id
    assert data["status"] in [
        TaskStatus.PENDING,
        TaskStatus.RUNNING,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
    ]
    assert "result" in data


@pytest.mark.asyncio
async def test_get_task_assets(client: AsyncClient, db_session: AsyncSession):
    """
    Test retrieving assets discovered by a task.
    GET /tasks/{id}/assets
    """
    # 1. Setup Task
    resp = await client.post("/api/v1/projects/", json={"name": "Assets Proj"})
    project_id = resp.json()["id"]
    resp = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "T", "url": "http://example.com"},
    )
    target_id = resp.json()["id"]
    resp = await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")
    task_id = resp.json()["task_id"]

    # 2. Mock some assets (manually insert to DB for this task)
    from app.models.asset import Asset, AssetType, AssetSource, AssetDiscovery
    from app.core.utils import utc_now

    # We need the task_id (DB ID) to link AssetDiscovery.
    # The API returns task_id (DB ID).

    # Create Asset
    asset = Asset(
        target_id=target_id,
        content_hash="hash123",
        type=AssetType.URL,
        source=AssetSource.HTML,
        method="GET",
        url="http://example.com/found",
        path="/found",
        first_seen_at=utc_now(),
        last_seen_at=utc_now(),
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    # Link to Task via AssetDiscovery
    discovery = AssetDiscovery(
        task_id=task_id, asset_id=asset.id, discovered_at=utc_now()
    )
    db_session.add(discovery)
    await db_session.commit()

    # 3. Get Assets
    resp = await client.get(f"/api/v1/tasks/{task_id}/assets")

    # EXPECT FAIL (404)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["url"] == "http://example.com/found"
