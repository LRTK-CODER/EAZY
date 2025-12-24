from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {"status": "ok"}
