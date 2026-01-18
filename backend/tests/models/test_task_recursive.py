"""
Test 1.1: Task Recursive Fields (RED Phase)
Expected to FAIL: AttributeError for depth, max_depth, parent_task_id
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskType


@pytest.mark.asyncio
async def test_task_has_depth_field_default_zero(db_session: AsyncSession):
    """
    Given: 새 Task 생성
    When: depth 미지정
    Then: 기본값 0
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)

    # This should FAIL: AttributeError: 'Task' has no attribute 'depth'
    assert hasattr(task, "depth"), "Task should have depth field"
    assert task.depth == 0, "depth should default to 0"


@pytest.mark.asyncio
async def test_task_has_max_depth_field_default_three(db_session: AsyncSession):
    """
    Given: 새 Task 생성
    When: max_depth 미지정
    Then: 기본값 3
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)

    # This should FAIL: AttributeError: 'Task' has no attribute 'max_depth'
    assert hasattr(task, "max_depth"), "Task should have max_depth field"
    assert task.max_depth == 3, "max_depth should default to 3"


@pytest.mark.asyncio
async def test_task_has_parent_task_id_nullable(db_session: AsyncSession):
    """
    Given: 루트 Task
    When: parent_task_id=None
    Then: 정상 생성
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = Task(project_id=project.id, type=TaskType.CRAWL, status=TaskStatus.PENDING)

    # This should FAIL: AttributeError: 'Task' has no attribute 'parent_task_id'
    assert hasattr(task, "parent_task_id"), "Task should have parent_task_id field"
    assert task.parent_task_id is None, "parent_task_id should be None for root task"


@pytest.mark.asyncio
async def test_task_depth_persists_in_db(db_session: AsyncSession):
    """
    Given: Task with depth=2
    When: 저장 후 조회
    Then: depth=2 유지
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
        depth=2,
        max_depth=5,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.depth == 2
    assert task.max_depth == 5


@pytest.mark.asyncio
async def test_task_parent_task_id_foreign_key(db_session: AsyncSession):
    """
    Given: 부모 Task와 자식 Task
    When: 자식 Task에 parent_task_id 설정
    Then: 정상 저장 및 참조
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create parent task
    parent_task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.COMPLETED,
        depth=0,
        max_depth=3,
    )
    db_session.add(parent_task)
    await db_session.commit()
    await db_session.refresh(parent_task)

    # Create child task with parent_task_id
    child_task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
        depth=1,
        max_depth=3,
        parent_task_id=parent_task.id,
    )
    db_session.add(child_task)
    await db_session.commit()
    await db_session.refresh(child_task)

    assert child_task.parent_task_id == parent_task.id
    assert child_task.depth == parent_task.depth + 1


@pytest.mark.asyncio
async def test_task_parent_task_id_set_null_on_parent_delete(db_session: AsyncSession):
    """
    Given: 부모-자식 Task 관계
    When: 부모 Task 삭제
    Then: 자식 Task의 parent_task_id=NULL (CASCADE 아님, SET NULL)
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create parent task
    parent_task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.COMPLETED,
        depth=0,
        max_depth=3,
    )
    db_session.add(parent_task)
    await db_session.commit()
    await db_session.refresh(parent_task)

    parent_task_id = parent_task.id

    # Create child task
    child_task = Task(
        project_id=project.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
        depth=1,
        max_depth=3,
        parent_task_id=parent_task_id,
    )
    db_session.add(child_task)
    await db_session.commit()
    await db_session.refresh(child_task)

    child_task_id = child_task.id

    # Delete parent task
    await db_session.delete(parent_task)
    await db_session.commit()

    # Expire all cached objects to force fresh load from DB
    db_session.expire_all()

    # Refresh child task to get updated state
    from sqlmodel import select

    statement = select(Task).where(Task.id == child_task_id)
    result = await db_session.exec(statement)
    updated_child = result.one()

    # Child should still exist with parent_task_id=NULL
    assert updated_child is not None
    assert updated_child.parent_task_id is None
