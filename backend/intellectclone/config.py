"""
Configuración centralizada del sistema via variables de entorno.
Usa Pydantic Settings para validación estricta al arrancar.
"""

from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -------------------------------------------------------------------------
    # Entorno
    # -------------------------------------------------------------------------
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # -------------------------------------------------------------------------
    # Base de datos
    # -------------------------------------------------------------------------
    database_url: PostgresDsn

    # -------------------------------------------------------------------------
    # Redis / Celery
    # -------------------------------------------------------------------------
    redis_url: RedisDsn

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_allowed_origins: list[str] = ["http://localhost:3000"]

    # -------------------------------------------------------------------------
    # LLMs — API keys
    # -------------------------------------------------------------------------
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # Modelo default del sistema (R8: Claude Sonnet 4.6)
    llm_modelo_default: str = "anthropic:claude-sonnet-4-6"

    # Presupuesto mensual en USD
    llm_presupuesto_mensual_usd: float = 500.0
    llm_alerta_porcentaje: int = 80

    # -------------------------------------------------------------------------
    # Almacenamiento
    # -------------------------------------------------------------------------
    storage_path: str = "/var/intellectclone/storage"

    # -------------------------------------------------------------------------
    # Cosecha
    # -------------------------------------------------------------------------
    openalex_polite_email: str = ""
    ror_id_uat: str = "https://ror.org/04hhneb29"

    # -------------------------------------------------------------------------
    # Admin
    # -------------------------------------------------------------------------
    admin_secret_key: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_SECRET no puede estar vacío")
        return v


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia cacheada de configuración."""
    return Settings()
