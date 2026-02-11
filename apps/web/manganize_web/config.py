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
    upload_ttl_hours: int = 24

    # Object storage (S3-compatible: AWS S3 / Cloudflare R2 / MinIO)
    storage_provider: Literal["s3", "r2", "minio"] = "s3"
    storage_bucket: str = "manganize-uploads"
    storage_region: str = "ap-northeast-1"
    storage_endpoint_url: str | None = None
    storage_access_key_id: str | None = None
    storage_secret_access_key: str | None = None
    storage_force_path_style: bool = False
    storage_object_prefix: str = "uploads"
    storage_signed_url_ttl_seconds: int = 900

    # CORS
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]


# Global settings instance
settings = Settings()
