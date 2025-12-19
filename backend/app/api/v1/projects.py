from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import project_service

router = APIRouter()

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
