from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers

# Initialize Logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)

# Setup Middleware (CORS, Request Logging)
setup_middleware(app)

# Setup Exception Handlers
setup_exception_handlers(app)

@app.get("/")
def read_root():
    return {"Hello": "World", "Project": settings.PROJECT_NAME}
