from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.llm_config import LLMConfigCreate, LLMConfigResponse
from app.services.llm_service import llm_service
from app.services.project_service import project_service

router = APIRouter()

@router.post("/{project_id}/llm-config", response_model=LLMConfigResponse)
def upsert_llm_config(
    project_id: int,
    config_in: LLMConfigCreate,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return llm_service.upsert_llm_config(db, project_id, config_in)

@router.get("/{project_id}/llm-config", response_model=LLMConfigResponse)
def get_llm_config(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    config = llm_service.get_llm_config(db, project_id)
    if not config:
        # Return empty/default or 404? 
        # Typically 404 if not found, let frontend handle "Not Configured" state
        raise HTTPException(status_code=404, detail="LLM Config not found")
        
    return config
