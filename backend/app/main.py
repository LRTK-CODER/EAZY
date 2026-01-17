import logging
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.cors import get_cors_origins, validate_cors_config
from app.core.exceptions import ScanError
from app.api.v1.endpoints import project, task

logger = logging.getLogger(__name__)

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
    allow_methods=(
        settings.CORS_ALLOW_METHODS.split(",")
        if settings.CORS_ALLOW_METHODS != "*"
        else ["*"]
    ),
    allow_headers=(
        settings.CORS_ALLOW_HEADERS.split(",")
        if settings.CORS_ALLOW_HEADERS != "*"
        else ["*"]
    ),
)

api_router = APIRouter()
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
# Nested router structure in project.py covers /projects/{id}/targets
# But we defined trigger_scan as top level /projects/... in task.py for now?
# Or we can put it under /api/v1 directly as defined in router.

# Wait, the failing test uses: /api/v1/projects/{project_id}/targets/{target_id}/scan
# So we can just include it.
api_router.include_router(task.router, tags=["tasks"])

app.include_router(api_router, prefix=settings.API_V1_STR)


# Global Exception Handlers
@app.exception_handler(ScanError)
async def scan_error_handler(request: Request, exc: ScanError) -> JSONResponse:
    """Handle all ScanError subclasses with appropriate HTTP status codes."""
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        "ScanError: %s (status=%d, error=%s)",
        exc.message,
        exc.status_code,
        exc.error_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without leaking internal details."""
    logger.exception("Unexpected error: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "detail": None,
        },
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {"status": "ok"}
