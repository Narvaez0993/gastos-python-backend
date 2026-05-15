"""Pruebas unitarias del repositorio SQL crudo de movimientos de fuentes."""

import pytest

from app.repositories.sql.money_source_movement_sql_repository import (
    MoneySourceMovementSqlRepository,
)
from app.repositories.sql.money_source_sql_repository import MoneySourceSqlRepository
from app.repositories.sql.user_sql_repository import UserSqlRepository


@pytest.fixture
def source_id(tmp_sqlite_path):
    user = UserSqlRepository(db_path=tmp_sqlite_path).create(
        name="Sebastian", email="seba@example.com", password_hash="h"
    )
    source = MoneySourceSqlRepository(db_path=tmp_sqlite_path).create(
        user["id"], "Nequi", "nequi", balance=1000
    )
    return source["id"]


def test_create_devuelve_movimiento_con_balances(tmp_sqlite_path, source_id):
    repo = MoneySourceMovementSqlRepository(db_path=tmp_sqlite_path)
    movement = repo.create(
        money_source_id=source_id,
        movement_type="deposit",
        amount=500,
        balance_before=1000,
        balance_after=1500,
        date="2026-05-09T12:00:00+00:00",
    )
    assert movement["balance_before"] == 1000
    assert movement["balance_after"] == 1500
    assert movement["type"] == "deposit"


def test_has_movements_detecta_correctamente(tmp_sqlite_path, source_id):
    repo = MoneySourceMovementSqlRepository(db_path=tmp_sqlite_path)
    assert repo.has_movements(source_id) is False
    repo.create(
        money_source_id=source_id, movement_type="deposit", amount=100,
        balance_before=1000, balance_after=1100,
        date="2026-05-09T12:00:00+00:00",
    )
    assert repo.has_movements(source_id) is True


def test_get_filtered_pagina_resultados(tmp_sqlite_path, source_id):
    repo = MoneySourceMovementSqlRepository(db_path=tmp_sqlite_path)
    for i in range(5):
        repo.create(
            money_source_id=source_id, movement_type="deposit", amount=100,
            balance_before=i * 100, balance_after=(i + 1) * 100,
            date=f"2026-05-{i + 1:02d}T12:00:00+00:00",
        )

    page1 = repo.get_filtered(source_id, page=1, limit=2)
    assert len(page1["movements"]) == 2
    assert page1["pagination"]["total"] == 5
    assert page1["pagination"]["pages"] == 3
