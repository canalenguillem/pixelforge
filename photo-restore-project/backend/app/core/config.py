"""Configuración central de la aplicación (cargada desde variables de entorno).

Usa pydantic-settings para validar y tipar todas las env vars.
NO contiene lógica de negocio — solo definición de settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la aplicación, poblados desde el entorno / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App -----------------------------------------------------------------
    PROJECT_NAME: str = "Photo Restore Pro"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Registro público abierto. Desactivado: el alta será por invitación (link).
    # Reactivar poniendo ALLOW_REGISTRATION=true en el entorno cuando exista.
    ALLOW_REGISTRATION: bool = False

    # --- URLs ----------------------------------------------------------------
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Databases -----------------------------------------------------------
    # docker-compose inyecta DATABASE_URL / MONGODB_URL / REDIS_URL directamente.
    DATABASE_URL: str = "mysql+pymysql://photo_restore_user:secure_password_123@mariadb:3306/photo_restore"
    MONGODB_URL: str = "mongodb://photo_restore_user:mongo_secure_123@mongodb:27017/photo_restore_jobs?authSource=admin"
    MONGO_DB: str = "photo_restore_jobs"
    REDIS_URL: str = "redis://redis:6379"
    REDIS_PASSWORD: str = ""

    # --- JWT -----------------------------------------------------------------
    JWT_SECRET_KEY: str = "change_me_in_production_32_chars_min"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # --- ComfyUI -------------------------------------------------------------
    # Valor por defecto genérico; sobrescribir en .env (p. ej. IP de tu ComfyUI en LAN).
    COMFYUI_DEFAULT_URL: str = "http://host.docker.internal:8188"
    COMFYUI_API_KEY: str = ""

    # --- LLM APIs ------------------------------------------------------------
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # --- Storage -------------------------------------------------------------
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_FOLDER: str = "/app/uploads"
    PROCESSED_FOLDER: str = "/app/processed"
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,bmp,tiff"

    # --- Security ------------------------------------------------------------
    ENCRYPTION_KEY: str = "your_32_character_encryption_key_"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Logging -------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS como lista (separada por comas en la env var)."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_set(self) -> set[str]:
        """Extensiones permitidas como set en minúsculas."""
        return {ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()}


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de Settings (singleton)."""
    return Settings()


settings = get_settings()
