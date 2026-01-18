import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """
    Test the health check endpoint.
    Should return 200 OK and {"status": "ok"}.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_swagger_ui(client):
    """Test that Swagger UI is accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200
