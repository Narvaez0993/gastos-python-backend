"""Fixtures globales para las pruebas unitarias.

- tmp_sqlite_path: archivo SQLite temporal con el mismo schema que producción
  (para repositorios SQL).
- db_session: sesión SQLAlchemy en memoria con Base.metadata.create_all
  (para repositorios JPA).
- mock_*_repo: MagicMock con spec de la interfaz correspondiente
  (para pruebas de servicios sin tocar BD).
- auth_service, test_user, auth_headers: fixtures para tests que requieren
  autenticación JWT.
"""

import os
import sqlite3
from typing import Generator
from unittest.mock import MagicMock

import pytest

# Forzar secret de test antes de cualquier import de settings.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod-0000000000000000")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # acelerar tests

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import SCHEMA_SQL
from app.db.base import Base
from app.db.models import MoneySource, User  # noqa: F401  (registrar en metadata)
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.user_repository import IUserRepository
from app.repositories.sql.user_sql_repository import UserSqlRepository
from app.services.auth_service import AuthService


@pytest.fixture
def tmp_sqlite_path(tmp_path) -> str:
    """Archivo SQLite efímero con el mismo DDL de producción."""
    db_file = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    return db_file


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesión SQLAlchemy en memoria con todas las tablas de los modelos creadas."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=IUserRepository)


@pytest.fixture
def mock_money_source_repo():
    return MagicMock(spec=IMoneySourceRepository)


@pytest.fixture
def mock_expense_repo():
    return MagicMock(spec=IExpenseRepository)


@pytest.fixture
def mock_budget_repo():
    return MagicMock(spec=IBudgetRepository)


@pytest.fixture
def mock_movement_repo():
    return MagicMock(spec=IMoneySourceMovementRepository)


@pytest.fixture
def auth_service(mock_user_repo) -> AuthService:
    """AuthService con repo mockeado. Útil para tests unitarios."""
    return AuthService(mock_user_repo)


@pytest.fixture
def auth_service_sql(tmp_sqlite_path) -> AuthService:
    """AuthService respaldado por UserSqlRepository sobre BD temporal real.
    Útil para tests de integración del flujo register/login."""
    return AuthService(UserSqlRepository(db_path=tmp_sqlite_path))


@pytest.fixture
def test_user(auth_service_sql) -> dict:
    """Crea un user de prueba via AuthService y devuelve el dict público."""
    from app.schemas.auth import RegisterRequest

    user, _token, _expires = auth_service_sql.register_user(
        RegisterRequest(
            email="test@example.com",
            password="secret123",
            name="Test User",
        )
    )
    return user


@pytest.fixture
def auth_headers(auth_service_sql, test_user) -> dict:
    """Authorization header con un Bearer JWT válido del test_user."""
    token, _expires = auth_service_sql.create_access_token(test_user["id"])
    return {"Authorization": f"Bearer {token}"}
