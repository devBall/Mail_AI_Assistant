from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str
    ENVIRONMENT: str
    DEBUG: bool
    API_PREFIX: str
    
@lru_cache()
def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()