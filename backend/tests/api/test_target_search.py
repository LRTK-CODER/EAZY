"""Tests for GET /projects/{project_id}/targets/search endpoint - TDD Red Phase."""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_search_targets_by_name(client: AsyncClient, db_session: AsyncSession):
    """q=api -> name에 'api' 포함된 Target 반환"""
    # Setup: Project 생성
    resp = await client.post("/api/v1/projects/", json={"name": "Search Test Proj"})
    project_id = resp.json()["id"]

    # Target 3개 생성: 2개는 name에 'api' 포함, 1개는 미포함
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Main API Server", "url": "https://main.example.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "REST API Gateway", "url": "https://gateway.example.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Frontend App", "url": "https://app.example.com"},
    )

    # Act: name에 'api' 포함된 Target 검색
    resp = await client.get(f"/api/v1/projects/{project_id}/targets/search?q=api")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    names = [item["name"] for item in data["items"]]
    assert all("api" in name.lower() for name in names)


@pytest.mark.asyncio
async def test_search_targets_by_url(client: AsyncClient, db_session: AsyncSession):
    """q=example.com -> URL에 'example.com' 포함된 Target 반환"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "URL Search Proj"})
    project_id = resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Example Site", "url": "https://www.example.com/app"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Other Site", "url": "https://other.io/page"},
    )

    # Act: URL에 'example.com' 포함된 Target 검색
    resp = await client.get(
        f"/api/v1/projects/{project_id}/targets/search?q=example.com"
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert "example.com" in data["items"][0]["url"]


@pytest.mark.asyncio
async def test_search_targets_case_insensitive(
    client: AsyncClient, db_session: AsyncSession
):
    """q=myapplication -> 'MyApplication' 찾음 (대소문자 무시)"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Case Test Proj"})
    project_id = resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "MyApplication Server", "url": "https://myapp.example.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Other Target", "url": "https://other.example.com"},
    )

    # Act: 소문자로 검색
    resp = await client.get(
        f"/api/v1/projects/{project_id}/targets/search?q=myapplication"
    )

    # Assert: 대소문자 무시하고 찾아야 함
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "MyApplication Server"


@pytest.mark.asyncio
async def test_search_targets_partial_match(
    client: AsyncClient, db_session: AsyncSession
):
    """q=aaaa -> 'https://aaaa.bbb' 찾음 (부분 일치)"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Partial Match Proj"})
    project_id = resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target A", "url": "https://aaaa.bbb.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Target B", "url": "https://cccc.ddd.com"},
    )

    # Act: 부분 문자열로 검색
    resp = await client.get(f"/api/v1/projects/{project_id}/targets/search?q=aaaa")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "aaaa" in data["items"][0]["url"]


@pytest.mark.asyncio
async def test_search_targets_project_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    """존재하지 않는 project_id -> 404 Not Found"""
    # Act: 존재하지 않는 project_id로 검색
    resp = await client.get("/api/v1/projects/99999/targets/search?q=test")

    # Assert
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_targets_project_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """다른 프로젝트의 Target은 검색되지 않음"""
    # Setup: 2개 프로젝트 생성
    resp = await client.post("/api/v1/projects/", json={"name": "Project A"})
    project_a_id = resp.json()["id"]

    resp = await client.post("/api/v1/projects/", json={"name": "Project B"})
    project_b_id = resp.json()["id"]

    # Project A에 Target 생성
    await client.post(
        f"/api/v1/projects/{project_a_id}/targets/",
        json={"name": "Shared Name API", "url": "https://a.example.com"},
    )

    # Project B에 Target 생성 (같은 이름 패턴)
    await client.post(
        f"/api/v1/projects/{project_b_id}/targets/",
        json={"name": "Shared Name API", "url": "https://b.example.com"},
    )

    # Act: Project A에서 검색
    resp = await client.get(f"/api/v1/projects/{project_a_id}/targets/search?q=Shared")

    # Assert: Project A의 Target만 반환
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["url"] == "https://a.example.com"


@pytest.mark.asyncio
async def test_search_targets_special_characters(
    client: AsyncClient, db_session: AsyncSession
):
    """q=api_v1 -> SQL LIKE 와일드카드(%, _) 이스케이프 처리"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Special Char Proj"})
    project_id = resp.json()["id"]

    # 정확히 'api_v1' 포함 Target
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "api_v1 server", "url": "https://api.example.com"},
    )
    # 'api1v1', 'apixv1' 등 (_가 와일드카드로 해석되면 매칭될 수 있는 패턴)
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "api1v1 server", "url": "https://other.example.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "apixv1 server", "url": "https://another.example.com"},
    )

    # Act: 'api_v1' 검색 (_는 이스케이프되어 정확히 매칭)
    resp = await client.get(f"/api/v1/projects/{project_id}/targets/search?q=api_v1")

    # Assert: 정확히 'api_v1' 포함된 것만 반환 (와일드카드 X)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "api_v1 server"


@pytest.mark.asyncio
async def test_search_targets_pagination(client: AsyncClient, db_session: AsyncSession):
    """skip=2&limit=3 -> 올바른 페이지네이션"""
    # Setup: 5개 Target 생성
    resp = await client.post("/api/v1/projects/", json={"name": "Pagination Proj"})
    project_id = resp.json()["id"]

    for i in range(5):
        await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": f"API Target {i}", "url": f"https://api{i}.example.com"},
        )

    # Act: skip=2, limit=2로 검색
    resp = await client.get(
        f"/api/v1/projects/{project_id}/targets/search?q=API&skip=2&limit=2"
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2  # limit 적용
    assert data["total"] == 5  # total은 전체 매칭 개수


@pytest.mark.asyncio
async def test_search_targets_empty_result(
    client: AsyncClient, db_session: AsyncSession
):
    """매칭 없음 -> 200 OK with {items: [], total: 0}"""
    # Setup
    resp = await client.post("/api/v1/projects/", json={"name": "Empty Result Proj"})
    project_id = resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/targets/",
        json={"name": "Some Target", "url": "https://example.com"},
    )

    # Act: 매칭되지 않는 검색어
    resp = await client.get(
        f"/api/v1/projects/{project_id}/targets/search?q=nonexistent_xyz_123"
    )

    # Assert: 200 OK, 빈 결과
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
