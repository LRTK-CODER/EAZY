from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.logging import logger

def setup_exception_handlers(app: FastAPI):
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("global_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "details": str(exc)},
        )
