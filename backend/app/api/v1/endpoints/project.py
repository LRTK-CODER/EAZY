from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.project import Project, ProjectCreate, ProjectRead, ProjectUpdate
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
    archived: bool = False,
    session: AsyncSession = Depends(get_session)
):
    service = ProjectService(session)
    return await service.get_projects(skip=skip, limit=limit, archived=archived)

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

@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an existing project"""
    service = ProjectService(session)
    updated_project = await service.update_project(project_id, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    permanent: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """Delete a project (soft delete by default, permanent if permanent=true)"""
    service = ProjectService(session)

    if permanent:
        # Hard delete (Archived 페이지에서만 사용)
        deleted = await service.delete_project_permanent(project_id)
    else:
        # Soft delete (일반 삭제 - Archive로 이동)
        deleted = await service.archive_project(project_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return

@router.patch("/{project_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_project(
    project_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Restore an archived project"""
    service = ProjectService(session)
    restored = await service.restore_project(project_id)
    if not restored:
        raise HTTPException(status_code=404, detail="Project not found")
    return

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

@router.get("/{project_id}/targets/{target_id}", response_model=TargetRead)
async def read_target(
    project_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_session)
):
    # Verify project exists first
    project_service = ProjectService(session)
    if not await project_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    # Get the specific target
    service = TargetService(session)
    target = await service.get_target(target_id)

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Verify target belongs to the project
    if target.project_id != project_id:
        raise HTTPException(status_code=404, detail="Target not found")

    return target

@router.delete("/{project_id}/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    project_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_session)
):
    service = TargetService(session)
    # Ideally check project_id match too, but for MVP simple ID check
    result = await service.delete_target(target_id)
    if not result:
        raise HTTPException(status_code=404, detail="Target not found")
    return

from app.models.target import TargetUpdate

@router.patch("/{project_id}/targets/{target_id}", response_model=TargetRead)
async def update_target(
    project_id: int,
    target_id: int,
    target_in: TargetUpdate,
    session: AsyncSession = Depends(get_session)
):
    service = TargetService(session)
    updated_target = await service.update_target(target_id, target_in)
    if not updated_target:
        raise HTTPException(status_code=404, detail="Target not found")
    return updated_target
