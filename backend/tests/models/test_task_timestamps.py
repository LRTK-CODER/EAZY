"""
Test 5-Imp.1: Task Timestamps & Cancellation Model Tests (RED Phase)
Expected to FAIL: AttributeError for started_at, completed_at, CANCELLED status
"""
import pytest
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType, TaskStatus


@pytest.mark.asyncio
async def test_task_has_started_at_field(db_session: AsyncSession):
    """Test Task model has started_at field - RED Phase"""
    # Setup project first
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create task
    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)

    # This should FAIL: AttributeError: 'Task' has no attribute 'started_at'
    assert hasattr(task, 'started_at'), "Task should have started_at field"
    assert task.started_at is None, "started_at should be None initially"


@pytest.mark.asyncio
async def test_task_has_completed_at_field(db_session: AsyncSession):
    """Test Task model has completed_at field - RED Phase"""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)

    # This should FAIL: AttributeError: 'Task' has no attribute 'completed_at'
    assert hasattr(task, 'completed_at'), "Task should have completed_at field"
    assert task.completed_at is None, "completed_at should be None initially"


@pytest.mark.asyncio
async def test_task_status_has_cancelled_value(db_session: AsyncSession):
    """Test TaskStatus enum has CANCELLED value - RED Phase"""
    # This should FAIL: AttributeError: 'TaskStatus' has no attribute 'CANCELLED'
    assert hasattr(TaskStatus, 'CANCELLED'), "TaskStatus should have CANCELLED value"
    assert TaskStatus.CANCELLED == "cancelled"


@pytest.mark.asyncio
async def test_task_started_at_auto_set_on_running(db_session: AsyncSession):
    """Test started_at timestamp is set when task starts running - RED Phase"""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create task with PENDING status
    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Verify started_at is None
    assert task.started_at is None

    # Change status to RUNNING
    task.status = TaskStatus.RUNNING
    # Manually set started_at (this would be done in service layer)
    from app.models.task import utc_now
    task.started_at = utc_now()
    await db_session.commit()
    await db_session.refresh(task)

    # Verify started_at is set
    assert task.started_at is not None
    assert isinstance(task.started_at, datetime)


@pytest.mark.asyncio
async def test_task_completed_at_auto_set_on_completion(db_session: AsyncSession):
    """Test completed_at timestamp is set when task completes - RED Phase"""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create task with RUNNING status
    from app.models.task import utc_now
    task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.RUNNING,
        started_at=utc_now()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Verify completed_at is None
    assert task.completed_at is None

    # Change status to COMPLETED
    task.status = TaskStatus.COMPLETED
    task.completed_at = utc_now()
    await db_session.commit()
    await db_session.refresh(task)

    # Verify completed_at is set
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)


@pytest.mark.asyncio
async def test_task_completed_at_set_on_cancellation(db_session: AsyncSession):
    """Test completed_at timestamp is set when task is cancelled - RED Phase"""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create task with RUNNING status
    from app.models.task import utc_now
    task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.RUNNING,
        started_at=utc_now()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Change status to CANCELLED (should fail - enum value doesn't exist)
    task.status = TaskStatus.CANCELLED
    task.completed_at = utc_now()
    await db_session.commit()
    await db_session.refresh(task)

    # Verify status is CANCELLED and completed_at is set
    assert task.status == TaskStatus.CANCELLED
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)
