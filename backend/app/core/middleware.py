import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import logger

def setup_middleware(app: FastAPI):
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request Logging Middleware can be added here or as a separate middleware function
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log Request
        struct_logger = logger.bind(
            method=request.method,
            path=request.url.path,
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log Response
            struct_logger.info(
                "http_request",
                status_code=response.status_code,
                process_time=process_time,
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            struct_logger.error(
                "http_request_failed",
                error=str(e),
                process_time=process_time,
            )
            raise e
