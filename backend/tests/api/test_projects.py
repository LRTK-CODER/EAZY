import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_project(client):
    """Test creating a new project."""
    response = await client.post(
        "/api/v1/projects/",
        json={"name": "Test Project", "description": "Test Description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_read_projects(client):
    """Test reading list of projects."""
    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_project(client):
    """Test reading a specific project."""
    # First create a project
    create_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Single Project", "description": "Desc"}
    )
    project_id = create_res.json()["id"]

    # Then read it
    response = await client.get(f"/api/v1/projects/{project_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Single Project"

@pytest.mark.asyncio
async def test_update_project(client):
    """Test updating a project."""
    # Create project
    create_res = await client.post(
        "/api/v1/projects/",
        json={"name": "Original Name", "description": "Original"}
    )
    project_id = create_res.json()["id"]

    # Update it
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Original"  # Unchanged

@pytest.mark.asyncio
async def test_archive_project(client):
    """Test archiving a project (soft delete)."""
    # Create project
    create_res = await client.post(
        "/api/v1/projects/",
        json={"name": "To Archive", "description": ""}
    )
    project_id = create_res.json()["id"]

    # Archive it (soft delete)
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # Verify NOT in regular list
    list_res = await client.get("/api/v1/projects/")
    project_ids = [p["id"] for p in list_res.json()]
    assert project_id not in project_ids

    # Verify IS in archived list
    archived_res = await client.get("/api/v1/projects/?archived=true")
    archived_ids = [p["id"] for p in archived_res.json()]
    assert project_id in archived_ids

    # Verify still accessible by ID
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["is_archived"] == True

@pytest.mark.asyncio
async def test_delete_project_permanent(client):
    """Test permanently deleting a project (hard delete)."""
    # Create and archive project first
    create_res = await client.post(
        "/api/v1/projects/",
        json={"name": "To Delete Permanently", "description": ""}
    )
    project_id = create_res.json()["id"]

    # Archive it first
    await client.delete(f"/api/v1/projects/{project_id}")

    # Permanently delete it
    response = await client.delete(f"/api/v1/projects/{project_id}?permanent=true")
    assert response.status_code == 204

    # Verify completely gone
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 404

    # Verify NOT in archived list
    archived_res = await client.get("/api/v1/projects/?archived=true")
    archived_ids = [p["id"] for p in archived_res.json()]
    assert project_id not in archived_ids

@pytest.mark.asyncio
async def test_delete_nonexistent_project(client):
    """Test deleting a project that doesn't exist."""
    response = await client.delete("/api/v1/projects/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_restore_project(client):
    """Test restoring an archived project."""
    # Create and archive project
    create_res = await client.post(
        "/api/v1/projects/",
        json={"name": "To Restore", "description": ""}
    )
    project_id = create_res.json()["id"]
    await client.delete(f"/api/v1/projects/{project_id}")

    # Restore it
    response = await client.patch(f"/api/v1/projects/{project_id}/restore")
    assert response.status_code == 204

    # Verify back in regular list
    list_res = await client.get("/api/v1/projects/")
    project_ids = [p["id"] for p in list_res.json()]
    assert project_id in project_ids

    # Verify NOT in archived list
    archived_res = await client.get("/api/v1/projects/?archived=true")
    archived_ids = [p["id"] for p in archived_res.json()]
    assert project_id not in archived_ids

    # Verify archived_at is None
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.json()["archived_at"] is None
    assert get_res.json()["is_archived"] is False
