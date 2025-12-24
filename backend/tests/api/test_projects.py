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
