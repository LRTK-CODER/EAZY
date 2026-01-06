import hashlib
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app
from app.models.asset import Asset, AssetDiscovery
from app.models.task import Task


@pytest.mark.asyncio
async def test_create_target(client):
    """Test creating a target under a project."""
    # First create a project
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Target Project", "description": "For Target Test"}
    )
    project_id = proj_res.json()["id"]

    # Then create target
    response = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Test Target", "url": "https://example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Target"
    assert data["url"] == "https://example.com"
    assert data["project_id"] == project_id
    assert "id" in data

@pytest.mark.asyncio
async def test_read_targets(client):
    """Test reading targets of a project."""
    # Create project
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "List Project", "description": "Desc"}
    )
    project_id = proj_res.json()["id"]

    # Create target
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "T1", "url": "http://t1.com"}
    )

    # List targets
    response = await client.get(f"/api/v1/projects/{project_id}/targets/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


# ============================================================================
# Asset API Tests (TDD RED Phase)
# ============================================================================

@pytest.mark.asyncio
async def test_get_target_assets_endpoint_exists(client: AsyncClient):
    """Test 1: Verify the assets endpoint exists (returns status != 404)."""
    # Setup: Create Project + Target
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Asset Test Project", "description": "Testing assets endpoint"}
    )
    project_id = proj_res.json()["id"]

    target_res = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Test Target", "url": "https://example.com", "scope": "DOMAIN"}
    )
    target_id = target_res.json()["id"]

    # Execution: GET assets endpoint
    response = await client.get(f"/api/v1/projects/{project_id}/targets/{target_id}/assets")

    # Assertion: Endpoint should exist (not 404)
    assert response.status_code != 404, f"Expected endpoint to exist, got status {response.status_code}"


@pytest.mark.asyncio
async def test_get_target_assets_success(client: AsyncClient, db_session: AsyncSession):
    """Test 2: Verify successful response with Assets (200 OK, array with 3 different types)."""
    # Setup: Create Project + Target
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Success Test Project"}
    )
    project_id = proj_res.json()["id"]

    target_res = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Test Target", "url": "https://example.com", "scope": "DOMAIN"}
    )
    target_id = target_res.json()["id"]

    # Create Task
    task = Task(project_id=project_id, target_id=target_id, type="CRAWL", status="COMPLETED")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Create 3 Assets with different types
    now = datetime.utcnow()
    assets_data = [
        {
            "type": "URL",
            "method": "GET",
            "url": "https://example.com/page1",
            "path": "/page1"
        },
        {
            "type": "FORM",
            "method": "POST",
            "url": "https://example.com/login",
            "path": "/login"
        },
        {
            "type": "XHR",
            "method": "GET",
            "url": "https://example.com/api/data",
            "path": "/api/data"
        }
    ]

    created_assets = []
    for asset_data in assets_data:
        content_hash = hashlib.sha256(f"{asset_data['method']}:{asset_data['url']}".encode()).hexdigest()
        asset = Asset(
            target_id=target_id,
            content_hash=content_hash,
            type=asset_data["type"],
            source="HTML",
            method=asset_data["method"],
            url=asset_data["url"],
            path=asset_data["path"],
            first_seen_at=now,
            last_seen_at=now
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)
        created_assets.append(asset)

        # Create AssetDiscovery
        discovery = AssetDiscovery(task_id=task.id, asset_id=asset.id)
        db_session.add(discovery)

    await db_session.commit()

    # Execution: GET assets
    response = await client.get(f"/api/v1/projects/{project_id}/targets/{target_id}/assets")

    # Assertions
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be an array"
    assert len(data) == 3, f"Expected 3 assets, got {len(data)}"

    # Verify required fields
    for asset_json in data:
        assert "id" in asset_json
        assert "target_id" in asset_json
        assert "type" in asset_json
        assert "method" in asset_json
        assert "url" in asset_json
        assert "content_hash" in asset_json

    # Verify type diversity (AssetType enum values are lowercase)
    types = {asset_json["type"] for asset_json in data}
    assert "url" in types
    assert "form" in types
    assert "xhr" in types


@pytest.mark.asyncio
async def test_get_target_assets_target_not_found(client: AsyncClient):
    """Test 3: Verify 404 error when target does not exist."""
    # Setup: Create Project only (no Target)
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Project Without Target"}
    )
    project_id = proj_res.json()["id"]

    # Execution: GET assets for non-existent target
    response = await client.get(f"/api/v1/projects/{project_id}/targets/9999/assets")

    # Assertions
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Error response should contain 'detail' field"


@pytest.mark.asyncio
async def test_get_target_assets_project_not_found(client: AsyncClient):
    """Test 4: Verify 404 error when project does not exist."""
    # Execution: GET assets for non-existent project
    response = await client.get("/api/v1/projects/9999/targets/1/assets")

    # Assertions
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Error response should contain 'detail' field"


@pytest.mark.asyncio
async def test_get_target_assets_cross_project_isolation(client: AsyncClient, db_session: AsyncSession):
    """Test 5: Verify data isolation between projects (authorization check)."""
    # Setup: Create Project A → Target A1 → Asset A1
    proj_a_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Project A"}
    )
    project_a_id = proj_a_res.json()["id"]

    target_a1_res = await client.post(
        f"/api/v1/projects/{project_a_id}/targets/",
        json={"name": "Target A1", "url": "https://a.com", "scope": "DOMAIN"}
    )
    target_a1_id = target_a1_res.json()["id"]

    # Create Task A
    task_a = Task(project_id=project_a_id, target_id=target_a1_id, type="CRAWL", status="COMPLETED")
    db_session.add(task_a)
    await db_session.commit()
    await db_session.refresh(task_a)

    # Create Asset A1
    now = datetime.utcnow()
    content_hash_a = hashlib.sha256(b"GET:https://a.com/page").hexdigest()
    asset_a1 = Asset(
        target_id=target_a1_id,
        content_hash=content_hash_a,
        type="URL",
        source="HTML",
        method="GET",
        url="https://a.com/page",
        path="/page",
        first_seen_at=now,
        last_seen_at=now
    )
    db_session.add(asset_a1)
    await db_session.commit()
    await db_session.refresh(asset_a1)

    discovery_a = AssetDiscovery(task_id=task_a.id, asset_id=asset_a1.id)
    db_session.add(discovery_a)
    await db_session.commit()

    # Setup: Create Project B → Target B1 → Asset B1
    proj_b_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Project B"}
    )
    project_b_id = proj_b_res.json()["id"]

    target_b1_res = await client.post(
        f"/api/v1/projects/{project_b_id}/targets/",
        json={"name": "Target B1", "url": "https://b.com", "scope": "DOMAIN"}
    )
    target_b1_id = target_b1_res.json()["id"]

    # Create Task B
    task_b = Task(project_id=project_b_id, target_id=target_b1_id, type="CRAWL", status="COMPLETED")
    db_session.add(task_b)
    await db_session.commit()
    await db_session.refresh(task_b)

    # Create Asset B1
    content_hash_b = hashlib.sha256(b"GET:https://b.com/page").hexdigest()
    asset_b1 = Asset(
        target_id=target_b1_id,
        content_hash=content_hash_b,
        type="URL",
        source="HTML",
        method="GET",
        url="https://b.com/page",
        path="/page",
        first_seen_at=now,
        last_seen_at=now
    )
    db_session.add(asset_b1)
    await db_session.commit()
    await db_session.refresh(asset_b1)

    discovery_b = AssetDiscovery(task_id=task_b.id, asset_id=asset_b1.id)
    db_session.add(discovery_b)
    await db_session.commit()

    # Execution 1: Cross-project access (Project A accessing Target B1)
    response_cross = await client.get(f"/api/v1/projects/{project_a_id}/targets/{target_b1_id}/assets")

    # Assertion 1: Should return 404 (Target B1 does not belong to Project A)
    assert response_cross.status_code == 404, f"Expected 404 for cross-project access, got {response_cross.status_code}"

    # Execution 2: Valid access (Project A accessing Target A1)
    response_valid = await client.get(f"/api/v1/projects/{project_a_id}/targets/{target_a1_id}/assets")

    # Assertion 2: Should return only Asset A1
    assert response_valid.status_code == 200
    data = response_valid.json()
    assert len(data) == 1, f"Expected 1 asset, got {len(data)}"
    assert data[0]["id"] == asset_a1.id

    # Verify Asset B1 is NOT included
    asset_ids = [asset_json["id"] for asset_json in data]
    assert asset_b1.id not in asset_ids, "Asset B1 should not be accessible from Project A"


@pytest.mark.asyncio
async def test_get_target_assets_empty_list(client: AsyncClient):
    """Test 6: Verify empty list when no assets exist (no scan history)."""
    # Setup: Create Project + Target only (no Task/Asset)
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Empty Assets Project"}
    )
    project_id = proj_res.json()["id"]

    target_res = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target Without Scan", "url": "https://example.com", "scope": "DOMAIN"}
    )
    target_id = target_res.json()["id"]

    # Execution: GET assets
    response = await client.get(f"/api/v1/projects/{project_id}/targets/{target_id}/assets")

    # Assertions
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be an array"
    assert len(data) == 0, f"Expected empty list, got {len(data)} assets"


@pytest.mark.asyncio
async def test_get_target_assets_deduplication(client: AsyncClient, db_session: AsyncSession):
    """Test 7: Verify content_hash based deduplication (same asset discovered multiple times)."""
    # Setup: Create Project + Target
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Deduplication Test Project"}
    )
    project_id = proj_res.json()["id"]

    target_res = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Test Target", "url": "https://example.com", "scope": "DOMAIN"}
    )
    target_id = target_res.json()["id"]

    # Create Task 1
    task1 = Task(project_id=project_id, target_id=target_id, type="CRAWL", status="COMPLETED")
    db_session.add(task1)
    await db_session.commit()
    await db_session.refresh(task1)

    # Create Asset 1 (page1)
    now = datetime.utcnow()
    content_hash_1 = hashlib.sha256(b"GET:https://example.com/page1").hexdigest()
    asset1 = Asset(
        target_id=target_id,
        content_hash=content_hash_1,
        type="URL",
        source="HTML",
        method="GET",
        url="https://example.com/page1",
        path="/page1",
        first_seen_at=now,
        last_seen_at=now
    )
    db_session.add(asset1)
    await db_session.commit()
    await db_session.refresh(asset1)

    # Create AssetDiscovery 1
    discovery1 = AssetDiscovery(task_id=task1.id, asset_id=asset1.id)
    db_session.add(discovery1)
    await db_session.commit()

    # Create Task 2
    task2 = Task(project_id=project_id, target_id=target_id, type="CRAWL", status="COMPLETED")
    db_session.add(task2)
    await db_session.commit()
    await db_session.refresh(task2)

    # Re-discover Asset 1 in Task 2 (same content_hash → should NOT create new Asset)
    # Update last_seen_at
    asset1.last_seen_at = datetime.utcnow()
    db_session.add(asset1)

    # Create AssetDiscovery 2 (same asset, different task)
    discovery2 = AssetDiscovery(task_id=task2.id, asset_id=asset1.id)
    db_session.add(discovery2)
    await db_session.commit()

    # Create Task 3
    task3 = Task(project_id=project_id, target_id=target_id, type="CRAWL", status="COMPLETED")
    db_session.add(task3)
    await db_session.commit()
    await db_session.refresh(task3)

    # Create Asset 2 (page2, different hash)
    content_hash_2 = hashlib.sha256(b"GET:https://example.com/page2").hexdigest()
    asset2 = Asset(
        target_id=target_id,
        content_hash=content_hash_2,
        type="URL",
        source="HTML",
        method="GET",
        url="https://example.com/page2",
        path="/page2",
        first_seen_at=now,
        last_seen_at=now
    )
    db_session.add(asset2)
    await db_session.commit()
    await db_session.refresh(asset2)

    # Create AssetDiscovery 3
    discovery3 = AssetDiscovery(task_id=task3.id, asset_id=asset2.id)
    db_session.add(discovery3)
    await db_session.commit()

    # Execution: GET assets
    response = await client.get(f"/api/v1/projects/{project_id}/targets/{target_id}/assets")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2, f"Expected 2 unique assets (deduplication applied), got {len(data)}"

    # Verify Asset 1 appears only once
    asset_ids = [asset_json["id"] for asset_json in data]
    assert asset_ids.count(asset1.id) == 1, "Asset 1 should appear only once despite multiple discoveries"

    # Verify DB: Asset 1 has 2 discoveries, Asset 2 has 1 discovery
    result = await db_session.execute(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == asset1.id)
    )
    asset1_discoveries = result.scalars().all()
    assert len(asset1_discoveries) == 2, f"Asset 1 should have 2 discoveries, got {len(asset1_discoveries)}"

    result = await db_session.execute(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == asset2.id)
    )
    asset2_discoveries = result.scalars().all()
    assert len(asset2_discoveries) == 1, f"Asset 2 should have 1 discovery, got {len(asset2_discoveries)}"


@pytest.mark.asyncio
async def test_get_target_assets_sorted_by_last_seen_desc(client: AsyncClient, db_session: AsyncSession):
    """Test 8: Verify assets are sorted by last_seen_at in descending order (newest first)."""
    # Setup: Create Project + Target
    proj_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Sorting Test Project"}
    )
    project_id = proj_res.json()["id"]

    target_res = await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Test Target", "url": "https://example.com", "scope": "DOMAIN"}
    )
    target_id = target_res.json()["id"]

    # Create Task
    task = Task(project_id=project_id, target_id=target_id, type="CRAWL", status="COMPLETED")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Create 3 Assets with different last_seen_at timestamps
    base_time = datetime(2026, 1, 1, 10, 0, 0)

    # Asset 1: Oldest (10:00:00)
    content_hash_1 = hashlib.sha256(b"GET:https://example.com/page1").hexdigest()
    asset1 = Asset(
        target_id=target_id,
        content_hash=content_hash_1,
        type="URL",
        source="HTML",
        method="GET",
        url="https://example.com/page1",
        path="/page1",
        first_seen_at=base_time,
        last_seen_at=base_time  # 10:00:00
    )
    db_session.add(asset1)
    await db_session.commit()
    await db_session.refresh(asset1)

    discovery1 = AssetDiscovery(task_id=task.id, asset_id=asset1.id)
    db_session.add(discovery1)

    # Asset 2: Middle (12:00:00)
    content_hash_2 = hashlib.sha256(b"GET:https://example.com/page2").hexdigest()
    asset2 = Asset(
        target_id=target_id,
        content_hash=content_hash_2,
        type="URL",
        source="HTML",
        method="GET",
        url="https://example.com/page2",
        path="/page2",
        first_seen_at=base_time,
        last_seen_at=base_time + timedelta(hours=2)  # 12:00:00
    )
    db_session.add(asset2)
    await db_session.commit()
    await db_session.refresh(asset2)

    discovery2 = AssetDiscovery(task_id=task.id, asset_id=asset2.id)
    db_session.add(discovery2)

    # Asset 3: Newest (14:00:00)
    content_hash_3 = hashlib.sha256(b"GET:https://example.com/page3").hexdigest()
    asset3 = Asset(
        target_id=target_id,
        content_hash=content_hash_3,
        type="URL",
        source="HTML",
        method="GET",
        url="https://example.com/page3",
        path="/page3",
        first_seen_at=base_time,
        last_seen_at=base_time + timedelta(hours=4)  # 14:00:00
    )
    db_session.add(asset3)
    await db_session.commit()
    await db_session.refresh(asset3)

    discovery3 = AssetDiscovery(task_id=task.id, asset_id=asset3.id)
    db_session.add(discovery3)
    await db_session.commit()

    # Execution: GET assets
    response = await client.get(f"/api/v1/projects/{project_id}/targets/{target_id}/assets")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3, f"Expected 3 assets, got {len(data)}"

    # Verify order: Asset 3 (newest) → Asset 2 (middle) → Asset 1 (oldest)
    assert data[0]["id"] == asset3.id, f"First asset should be Asset 3 (newest), got {data[0]['id']}"
    assert data[1]["id"] == asset2.id, f"Second asset should be Asset 2 (middle), got {data[1]['id']}"
    assert data[2]["id"] == asset1.id, f"Third asset should be Asset 1 (oldest), got {data[2]['id']}"

    # Verify timestamps are in descending order
    timestamps = []
    for asset_json in data:
        # Parse ISO format timestamp (e.g., "2026-01-01T10:00:00" or with 'Z')
        ts_str = asset_json["last_seen_at"].replace('Z', '+00:00')
        if '+' not in ts_str:
            ts_str += '+00:00'
        timestamps.append(datetime.fromisoformat(ts_str))

    assert timestamps == sorted(timestamps, reverse=True), "Assets should be sorted by last_seen_at in descending order"
