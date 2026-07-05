from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI JOB INBOX ASSISTANT"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = '/api/v1'

    ai_classifier_mode: Literal["fallback", "anthropic"] = "fallback"
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-haiku-4-5-20251001"
    anthropic_max_tokens: int = 800

@lru_cache()
def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()