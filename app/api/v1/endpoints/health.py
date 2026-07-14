from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "app_name": settings.app_name, 
        "environment": settings.environment,
        "debug": settings.debug,
    }