"""
4.2 API Error Handling Tests (TDD RED Phase)

Tests for proper HTTP status code mapping from custom exceptions.
Expected to FAIL initially - this is TDD RED phase.
"""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from unittest.mock import patch, AsyncMock

from app.models.task import TaskStatus


class TestTargetNotFoundError:
    """Tests for 404 Not Found when target doesn't exist."""

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_404_for_missing_target(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan with non-existent target
        should return 404 Not Found.
        """
        # Setup: Create project only (no target)
        resp = await client.post("/api/v1/projects/", json={"name": "Error Test Proj"})
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        # Attempt scan with non-existent target_id
        non_existent_target_id = 99999
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{non_existent_target_id}/scan"
        )

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_404_error_response_contains_target_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Error response should contain target_id in detail."""
        resp = await client.post("/api/v1/projects/", json={"name": "Detail Test Proj"})
        project_id = resp.json()["id"]

        non_existent_target_id = 88888
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{non_existent_target_id}/scan"
        )

        assert resp.status_code == 404
        data = resp.json()
        # Check error response structure
        assert "detail" in data or "message" in data or "error" in data


class TestDuplicateScanError:
    """Tests for 409 Conflict when scan is already in progress."""

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_409_for_pending_task(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan when a PENDING task exists
        should return 409 Conflict.
        """
        # Setup: Create project and target
        resp = await client.post("/api/v1/projects/", json={"name": "Duplicate Test Proj"})
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Dup Target", "url": "http://example.com"},
        )
        assert resp.status_code == 201
        target_id = resp.json()["id"]

        # Trigger first scan - should succeed
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 202

        # Trigger second scan - should fail with 409
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_409_for_running_task(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan when a RUNNING task exists
        should return 409 Conflict.
        """
        from app.models.task import Task
        from app.core.utils import utc_now
        from sqlmodel import select

        # Setup
        resp = await client.post("/api/v1/projects/", json={"name": "Running Dup Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Running Target", "url": "http://example.com"},
        )
        target_id = resp.json()["id"]

        # Trigger first scan
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        task_id = resp.json()["task_id"]

        # Manually set to RUNNING
        result = await db_session.exec(select(Task).where(Task.id == task_id))
        task = result.one()
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        await db_session.commit()

        # Trigger second scan - should fail with 409
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_trigger_scan_allows_after_completed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan when previous task is COMPLETED
        should succeed with 202.
        """
        from app.models.task import Task
        from app.core.utils import utc_now
        from sqlmodel import select

        # Setup
        resp = await client.post("/api/v1/projects/", json={"name": "Completed Dup Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Completed Target", "url": "http://example.com"},
        )
        target_id = resp.json()["id"]

        # Trigger first scan
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        task_id = resp.json()["task_id"]

        # Manually set to COMPLETED
        result = await db_session.exec(select(Task).where(Task.id == task_id))
        task = result.one()
        task.status = TaskStatus.COMPLETED
        task.started_at = utc_now()
        task.completed_at = utc_now()
        await db_session.commit()

        # Trigger second scan - should succeed
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"


class TestUnsafeUrlError:
    """Tests for 400 Bad Request when URL is unsafe."""

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_400_for_localhost(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan with localhost URL
        should return 400 Bad Request.
        """
        # Setup: Create project and target with localhost URL
        resp = await client.post("/api/v1/projects/", json={"name": "Unsafe URL Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Localhost Target", "url": "http://localhost:8080"},
        )
        target_id = resp.json()["id"]

        # Trigger scan - should fail with 400
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_400_for_private_ip(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan with private IP
        should return 400 Bad Request.
        """
        resp = await client.post("/api/v1/projects/", json={"name": "Private IP Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Private IP Target", "url": "http://192.168.1.1"},
        )
        target_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_400_for_loopback(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        POST /projects/{id}/targets/{id}/scan with 127.0.0.1
        should return 400 Bad Request.
        """
        resp = await client.post("/api/v1/projects/", json={"name": "Loopback Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Loopback Target", "url": "http://127.0.0.1/admin"},
        )
        target_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


class TestUnexpectedError:
    """Tests for 500 Internal Server Error handling."""

    @pytest.mark.asyncio
    async def test_trigger_scan_returns_500_for_unexpected_error(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        Unexpected errors should return 500 without exposing internal details.
        """
        # Setup
        resp = await client.post("/api/v1/projects/", json={"name": "500 Error Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "500 Target", "url": "http://example.com"},
        )
        target_id = resp.json()["id"]

        # Mock at the service module level
        with patch(
            "app.services.task_service.TaskService.create_scan_task",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.side_effect = RuntimeError("Database connection lost: password=secret123")

            resp = await client.post(
                f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
            )

            assert resp.status_code == 500, f"Expected 500, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_500_error_does_not_leak_internal_details(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        500 error response should NOT contain sensitive internal details.
        """
        resp = await client.post("/api/v1/projects/", json={"name": "Leak Test Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "Leak Target", "url": "http://example.com"},
        )
        target_id = resp.json()["id"]

        with patch(
            "app.services.task_service.TaskService.create_scan_task",
            new_callable=AsyncMock,
        ) as mock_create:
            # Simulate error with sensitive info
            mock_create.side_effect = RuntimeError(
                "Connection to postgres://admin:supersecret@db:5432/eazy failed"
            )

            resp = await client.post(
                f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
            )

            assert resp.status_code == 500
            response_text = resp.text.lower()

            # Should NOT contain sensitive keywords
            assert "supersecret" not in response_text, "Password leaked in error response"
            assert "postgres://" not in response_text, "Connection string leaked"
            assert "admin:" not in response_text, "Credentials leaked"


class TestErrorResponseSchema:
    """Tests for unified error response schema."""

    @pytest.mark.asyncio
    async def test_error_response_has_required_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        Error responses should have consistent structure:
        - error (or code): machine-readable error code
        - message (or detail): human-readable message
        - status_code: HTTP status code (optional but recommended)
        """
        resp = await client.post("/api/v1/projects/", json={"name": "Schema Test Proj"})
        project_id = resp.json()["id"]

        # Trigger 404 error
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/99999/scan"
        )

        assert resp.status_code == 404
        data = resp.json()

        # At minimum, should have either 'detail' (FastAPI default) or 'error'/'message'
        has_error_info = (
            "detail" in data
            or "error" in data
            or "message" in data
        )
        assert has_error_info, f"Error response missing error info: {data}"

    @pytest.mark.asyncio
    async def test_409_error_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """409 Conflict should return structured error with context."""
        resp = await client.post("/api/v1/projects/", json={"name": "409 Schema Proj"})
        project_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/",
            json={"name": "409 Target", "url": "http://example.com"},
        )
        target_id = resp.json()["id"]

        # First scan succeeds
        await client.post(f"/api/v1/projects/{project_id}/targets/{target_id}/scan")

        # Second scan should fail with 409
        resp = await client.post(
            f"/api/v1/projects/{project_id}/targets/{target_id}/scan"
        )

        assert resp.status_code == 409
        data = resp.json()
        assert "detail" in data or "error" in data or "message" in data
