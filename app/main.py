from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    """Create FastAPI application instance."""
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app

app = create_app()
