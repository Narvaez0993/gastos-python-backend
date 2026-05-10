"""Fixtures globales para las pruebas unitarias.

- tmp_sqlite_path: archivo SQLite temporal con el mismo schema que produccion
  (para repositorios SQL).
- db_session: sesion SQLAlchemy en memoria con Base.metadata.create_all
  (para repositorios JPA).
- mock_*_repo: MagicMock con spec de la interfaz correspondiente
  (para pruebas de servicios sin tocar BD).
"""

import sqlite3
from typing import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import MoneySource, Person  # noqa: F401  (registrar en metadata)
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.person_repository import IPersonRepository


_DDL = """
    CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        date TEXT NOT NULL,
        money_source_id INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (person_id) REFERENCES persons(id),
        FOREIGN KEY (money_source_id) REFERENCES money_sources(id)
    );
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('daily', 'weekly', 'monthly')),
        amount REAL NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(person_id, type),
        FOREIGN KEY (person_id) REFERENCES persons(id)
    );
    CREATE TABLE IF NOT EXISTS money_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        name_normalized TEXT NOT NULL,
        balance REAL NOT NULL DEFAULT 0,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(person_id, name_normalized),
        FOREIGN KEY (person_id) REFERENCES persons(id)
    );
    CREATE TABLE IF NOT EXISTS money_source_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        money_source_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('expense', 'deposit', 'adjustment')),
        amount REAL NOT NULL,
        balance_before REAL NOT NULL,
        balance_after REAL NOT NULL,
        expense_id INTEGER,
        note TEXT,
        date TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (money_source_id) REFERENCES money_sources(id),
        FOREIGN KEY (expense_id) REFERENCES expenses(id)
    );
"""


@pytest.fixture
def tmp_sqlite_path(tmp_path) -> str:
    """Archivo SQLite efímero con el mismo DDL de producción."""
    db_file = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_DDL)
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
def mock_person_repo():
    return MagicMock(spec=IPersonRepository)


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
