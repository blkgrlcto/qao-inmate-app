"""API routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def api_root():
    """API root - returns service info."""
    return {"service": "qao-inmate-api", "version": "0.1.0"}
