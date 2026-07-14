from fastapi import APIRouter
from app.api.v1.endpoints import db_health, health, classifications

api_router = APIRouter()
api_router.include_router(
    health.router, 
    tags=["Health"]
)
api_router.include_router(
    classifications.router,
    tags=["Email Classification"]
)

api_router.include_router(
    db_health.router, 
    tags=["Database Health"]
)