from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.project import Project, ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    session: AsyncSession = Depends(get_session)
):
    service = ProjectService(session)
    return await service.create_project(project_in)

@router.get("/", response_model=List[ProjectRead])
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    service = ProjectService(session)
    return await service.get_projects(skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectRead)
async def read_project(
    project_id: int,
    session: AsyncSession = Depends(get_session)
):
    service = ProjectService(session)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

from app.models.target import TargetCreate, TargetRead
from app.services.target_service import TargetService

@router.post("/{project_id}/targets/", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
async def create_target(
    project_id: int,
    target_in: TargetCreate,
    session: AsyncSession = Depends(get_session)
):
    # Verify project exists first
    project_service = ProjectService(session)
    if not await project_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
        
    service = TargetService(session)
    return await service.create_target(project_id, target_in)

@router.get("/{project_id}/targets/", response_model=List[TargetRead])
async def read_targets(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    # Verify project exists first
    project_service = ProjectService(session)
    if not await project_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    service = TargetService(session)
    return await service.get_targets(project_id, skip=skip, limit=limit)
