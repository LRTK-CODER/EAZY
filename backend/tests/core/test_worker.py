import pytest
from sqlmodel import select

from app.core.queue import TaskManager
from app.models.asset import Asset
from app.models.task import Task, TaskStatus

# We will need to import the worker function, e.g.
# from app.worker import process_one_task


@pytest.mark.asyncio
async def test_worker_process_task(db_session, redis_client):
    """
    Test that the worker:
    1. Dequeues a task.
    2. Runs the crawler (we might mock this or use real one if acceptable).
    3. Updates Task status.
    4. Saves Assets.

    NOTE: We must clean the queue first to avoid stale tasks from previous runs.
    """
    await redis_client.delete("eazy_task_queue")

    # 0. Dependencies are already in db_session from conftest cleanup?
    # No, we need to create them.
    from app.models.project import Project
    from app.models.target import Target, TargetScope
    from app.models.task import TaskType

    project = Project(name="Worker Proj")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    target = Target(
        name="Worker Target",
        project_id=project.id,
        url="http://example.com",
        scope=TargetScope.DOMAIN,
    )
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    task = Task(
        project_id=project.id,
        target_id=target.id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    print(f"DEBUG TEST: Created Task ID: {task.id}")

    # 1. Enqueue Task manually (or via TaskManager)
    tm = TaskManager(redis_client)
    # Use the new signature
    await tm.enqueue_crawl_task(project.id, target.id, db_task_id=task.id)

    # 2. RUN WORKER (Import dynamically to allow test to exist before file)
    try:
        from app.services.crawler_service import CrawlerService
        from app.worker import process_one_task
    except ImportError:
        pytest.fail("Worker module 'app.worker' not found")

    # Mock CrawlerService to avoid spawning browser
    import unittest.mock

    with unittest.mock.patch.object(
        CrawlerService, "crawl", new_callable=unittest.mock.AsyncMock
    ) as mock_crawl:
        # CrawlerService.crawl() returns tuple (links, http_data)
        mock_crawl.return_value = (
            ["http://example.com/page1", "http://example.com/page2"],
            {},  # http_data (empty for this test)
        )
        processed = await process_one_task(db_session, tm)
    assert processed is True

    # 3. Verify DB Updates
    await db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None

    # 4. Verify Assets Created
    result = await db_session.exec(select(Asset).where(Asset.target_id == target.id))
    assets = result.all()
    assert len(assets) > 0
