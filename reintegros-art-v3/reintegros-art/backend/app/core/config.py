"""
Configuración central de la aplicación.
Lee variables de entorno y expone settings tipados.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Sistema Integral de Gestión de Reintegros ART"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./reintegros.db"

    # Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-A-LONG-RANDOM-STRING"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".jpg", ".jpeg", ".png"}

    # OCR / PDF
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "spa"  # español

    # IA (deshabilitado por defecto, base preparada)
    AI_EXTRACTION_ENABLED: bool = False
    ANTHROPIC_API_KEY: str = ""

    # SLA por defecto (en días hábiles)
    SLA_DEFAULT_DAYS: int = 5
    SLA_WARNING_HOURS: int = 48  # cuándo marcar como "próximo a vencer"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
