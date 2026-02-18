"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API service for qao-inmate-app",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["api"])


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and containers."""
    return {"status": "healthy"}
