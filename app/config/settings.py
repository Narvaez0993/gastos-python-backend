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

    PERSON_REPO_BACKEND: Literal["sql", "jpa"] = "jpa"
    MONEY_SOURCE_REPO_BACKEND: Literal["sql", "jpa"] = "jpa"

    DEFAULT_TIMEZONE: str = "America/Bogota"

    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('APP_ENV', 'dev')}",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista parseada de CORS_ORIGINS (separados por coma en .env)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

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
