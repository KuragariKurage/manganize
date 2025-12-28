"""Configuration management for Manganize Web Application"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./manganize.db"

    # Application
    app_title: str = "Manganize"
    app_description: str = "マンガ画像生成 Web アプリケーション"
    debug: bool = False
    environment: Literal["development", "production"] = "development"

    # Rate limiting
    rate_limit_per_minute: int = 10

    # File upload
    max_file_size_mb: int = 10
    allowed_file_extensions: list[str] = [".txt", ".pdf", ".md"]

    # CORS
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]


# Global settings instance
settings = Settings()
