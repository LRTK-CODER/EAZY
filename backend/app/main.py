from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="EAZY Backend",
    description="AI-Powered DAST Tool API",
    version="0.1.0",
)

# CORS Configuration
origins = ["*"]  # Allow all origins for MVP. In production, restrict this.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
