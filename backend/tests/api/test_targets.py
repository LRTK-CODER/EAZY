import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

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
