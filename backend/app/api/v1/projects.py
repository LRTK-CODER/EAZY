from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.target import TargetCreate, TargetResponse
from app.services.project_service import project_service
from app.services.target_service import target_service

router = APIRouter()

@router.post("/{project_id}/targets", response_model=TargetResponse)
def create_target(
    project_id: int,
    target_in: TargetCreate,
    db: Session = Depends(get_db)
):
    # Verify project exists first
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return target_service.create_target(db, project_id, target_in)

@router.get("/{project_id}/targets", response_model=list[TargetResponse])
def read_targets(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Verify project exists first
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return target_service.get_targets(db, project_id, skip=skip, limit=limit)

@router.post("/", response_model=ProjectResponse)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db)
):
    # Check for duplication (optional, based on unique constraint)
    # Using try-except or a check method in service is better, but keeping simple for now
    # Ideally service handles integrity errors
    return project_service.create_project(db, project_in)

@router.get("/", response_model=list[ProjectResponse])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    projects = project_service.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectCreate,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_service.update_project(db, project, project_in)

@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_service.delete_project(db, project)

# --- Target Endpoints (nested or direct) ---

@router.put("/{project_id}/targets/{target_id}", response_model=TargetResponse)
def update_target(
    project_id: int,
    target_id: int,
    target_in: TargetCreate,
    db: Session = Depends(get_db)
):
    # Verify project
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    target = target_service.get_target(db, target_id)
    if not target or target.project_id != project_id:
        raise HTTPException(status_code=404, detail="Target not found")
        
    return target_service.update_target(db, target, target_in)

@router.delete("/{project_id}/targets/{target_id}", response_model=TargetResponse)
def delete_target(
    project_id: int,
    target_id: int,
    db: Session = Depends(get_db)
):
    # Verify project
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target = target_service.get_target(db, target_id)
    if not target or target.project_id != project_id:
        raise HTTPException(status_code=404, detail="Target not found")

    return target_service.delete_target(db, target)
