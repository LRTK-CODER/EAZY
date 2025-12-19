from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.api.v1.projects import router as projects_router
from app.api.v1.llm_configs import router as llm_configs_router
from app.api.v1.api_keys import router as api_keys_router

# Initialize Logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)

# Setup Middleware (CORS, Request Logging)
setup_middleware(app)

# Setup Exception Handlers
setup_exception_handlers(app)

# Register Routers
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(llm_configs_router, prefix="/api/v1/projects", tags=["llm-configs"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["api-keys"])

@app.get("/")
def read_root():
    return {"Hello": "World", "Project": settings.PROJECT_NAME}
