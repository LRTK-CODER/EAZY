from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_session
from app.core.redis import get_redis
from app.services.task_service import TaskService
from app.models.task import Task, TaskRead
from app.models.asset import AssetRead

router = APIRouter()

@router.post("/projects/{project_id}/targets/{target_id}/scan", status_code=202)
async def trigger_scan(
    project_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
) -> dict:
    """
    Trigger a crawl/scan task for a specific target.
    """
    task_service = TaskService(session, redis)
    try:
        task = await task_service.create_scan_task(project_id, target_id)
        return {"status": "pending", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task_status(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    service = TaskService(session, redis)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks/{task_id}/assets", response_model=List[AssetRead])
async def get_task_assets(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    service = TaskService(session, redis)
    assets = await service.get_task_assets(task_id)
    return assets
