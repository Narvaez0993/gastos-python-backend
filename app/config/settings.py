"""Configuración tipada del proyecto cargada desde variables de entorno y .env."""

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación.

    El archivo .env cargado depende de la variable de entorno APP_ENV:
        - APP_ENV=dev  -> .env.dev (default)
        - APP_ENV=prod -> .env.prod
    """

    APP_ENV: Literal["dev", "prod", "test"] = "dev"

    DATABASE_PATH: str = "gastos.db"

    HOST: str = "0.0.0.0"
    PORT: int = 3002
    RELOAD: bool = True
    LOG_LEVEL: str = "info"

    SQL_ECHO: bool = False

    CORS_ORIGINS: str = "*"

    USER_REPO_BACKEND: Literal["sql", "jpa"] = "jpa"
    MONEY_SOURCE_REPO_BACKEND: Literal["sql", "jpa"] = "jpa"

    DEFAULT_TIMEZONE: str = "America/Bogota"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_EXPIRES_MINUTES: int = 1440
    BCRYPT_ROUNDS: int = 12

    ANTHROPIC_API_KEY: str = "***REMOVED***"
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    CLAUDE_MAX_TOKENS: int = 1024

    UPLOADS_DIR: str = "uploads"
    MAX_ATTACHMENT_MB: int = 10
    ALLOWED_ATTACHMENT_MIMES: str = (
        "image/jpeg,image/png,image/webp,image/heic,application/pdf"
    )

    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('APP_ENV', 'dev')}",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def model_post_init(self, __context) -> None:
        if self.APP_ENV == "prod" and (not self.JWT_SECRET or len(self.JWT_SECRET) < 32):
            raise ValueError(
                "JWT_SECRET es obligatorio en APP_ENV=prod y debe tener ≥32 caracteres. "
                "Generar con: openssl rand -hex 32"
            )

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista parseada de CORS_ORIGINS (separados por coma en .env)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_attachment_mimes_list(self) -> list[str]:
        return [m.strip() for m in self.ALLOWED_ATTACHMENT_MIMES.split(",") if m.strip()]

    def get_uploads_absolute_path(self) -> str:
        """Resuelve UPLOADS_DIR a ruta absoluta (anclada al root del proyecto si es relativa)."""
        if os.path.isabs(self.UPLOADS_DIR):
            return self.UPLOADS_DIR
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, self.UPLOADS_DIR)

    def get_database_absolute_path(self) -> str:
        """Resuelve DATABASE_PATH a ruta absoluta. Si es relativa, se ancla a la raíz del proyecto."""
        if os.path.isabs(self.DATABASE_PATH):
            return self.DATABASE_PATH
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, self.DATABASE_PATH)

    def get_database_url(self) -> str:
        """URL en formato SQLAlchemy a partir de la ruta absoluta."""
        return f"sqlite:///{self.get_database_absolute_path()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
