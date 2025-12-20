from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.api.v1.projects import router as projects_router
from app.api.v1.llm_configs import router as llm_configs_router
from app.api.v1.api_keys import router as api_keys_router

from contextlib import asynccontextmanager
import asyncio
from app.api.v1.proxy import router as proxy_router
from app.services.proxy_service import proxy_service
# Import models to register them with SQLAlchemy
from app.models.scan import ScanJob, Endpoint, Parameter # noqa: F401

# Initialize Logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    proxy_service.set_main_loop(asyncio.get_running_loop())
    yield
    # Shutdown
    proxy_service.stop()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Setup Middleware (CORS, Request Logging)
setup_middleware(app)

# Setup Exception Handlers
setup_exception_handlers(app)

# Register Routers
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(llm_configs_router, prefix="/api/v1/projects", tags=["llm-configs"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["api-keys"])
app.include_router(proxy_router, prefix="/api/v1/proxy", tags=["proxy"])

from app.api.v1.crawler import router as crawler_router
app.include_router(crawler_router, prefix="/api/v1/crawler", tags=["crawler"])

@app.get("/")
def read_root():
    return {"Hello": "World", "Project": settings.PROJECT_NAME}
