from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.api_key_service import api_key_service

router = APIRouter()

@router.post("/", response_model=ApiKeyResponse)
def create_api_key(
    key_in: ApiKeyCreate,
    db: Session = Depends(get_db)
):
    return api_key_service.create_api_key(db, key_in)

@router.get("/", response_model=list[ApiKeyResponse])
def get_api_keys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return api_key_service.get_api_keys(db, skip, limit)

@router.delete("/{key_id}")
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db)
):
    success = api_key_service.delete_api_key(db, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")
    return {"ok": True}
