from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.cors import get_cors_origins, validate_cors_config

app = FastAPI(
    title="EAZY Backend",
    description="AI-Powered DAST Tool API",
    version="0.1.0",
)

# CORS Configuration (Sprint 2.5)
origins = get_cors_origins()
validate_cors_config(origins, settings.ENVIRONMENT, settings.CORS_ALLOW_CREDENTIALS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS.split(",") if settings.CORS_ALLOW_METHODS != "*" else ["*"],
    allow_headers=settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS != "*" else ["*"],
)

from fastapi import APIRouter
from app.api.v1.endpoints import project, task

api_router = APIRouter()
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
# Nested router structure in project.py covers /projects/{id}/targets
# But we defined trigger_scan as top level /projects/... in task.py for now?
# Or we can put it under /api/v1 directly as defined in router.

# Wait, the failing test uses: /api/v1/projects/{project_id}/targets/{target_id}/scan
# So we can just include it.
api_router.include_router(task.router, tags=["tasks"])

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {"status": "ok"}
