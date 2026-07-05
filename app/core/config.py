from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI JOB INBOX ASSISTANT"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = '/api/v1'
    
    AI_CLASSIFIER_MODE: Literal["fallback", "anthropic"] = "fallback"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL:str = "claude-haiku-4-5-20251001"
    ANTHROPIC_MAX_TOKENS:int = 800
    
@lru_cache()
def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()