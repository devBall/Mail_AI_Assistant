from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME, 
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }