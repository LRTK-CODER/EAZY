import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

@pytest.mark.asyncio
async def test_delete_target(client: AsyncClient, db_session: AsyncSession):
    # 1. Create Project & Target
    p_resp = await client.post("/api/v1/projects/", json={"name": "Del Proj"})
    p_id = p_resp.json()["id"]
    t_resp = await client.post(f"/api/v1/projects/{p_id}/targets/", json={"name": "Del Target", "url": "http://del.com"})
    t_id = t_resp.json()["id"]
    
    # 2. Delete Target
    del_resp = await client.delete(f"/api/v1/projects/{p_id}/targets/{t_id}")
    assert del_resp.status_code == 204
    
    # 3. Verify Gone
    get_resp = await client.get(f"/api/v1/projects/{p_id}/targets/")
    targets = get_resp.json()
    assert len(targets) == 0

@pytest.mark.asyncio
async def test_update_target(client: AsyncClient, db_session: AsyncSession):
    # 1. Create Project & Target
    p_resp = await client.post("/api/v1/projects/", json={"name": "Upd Proj"})
    p_id = p_resp.json()["id"]
    t_resp = await client.post(f"/api/v1/projects/{p_id}/targets/", json={"name": "Old Name", "url": "http://old.com"})
    t_id = t_resp.json()["id"]
    
    # 2. Update Target
    patch_resp = await client.patch(f"/api/v1/projects/{p_id}/targets/{t_id}", json={
        "name": "New Name",
        "url": "http://new.com",
        "scope": "URL_ONLY"
    })
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "New Name"
    assert data["url"] == "http://new.com"
    assert data["scope"] == "URL_ONLY"
    
    # 3. Verify Persistence
    get_resp = await client.get(f"/api/v1/projects/{p_id}/targets/")
    targets = get_resp.json()
    assert targets[0]["name"] == "New Name"
