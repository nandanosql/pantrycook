from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "pantrycook",
        "version": "0.1.0",
        "llm_configured": settings.llm_configured,
    }
