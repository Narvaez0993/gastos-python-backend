"""Pruebas unitarias del repositorio SQL crudo de presupuestos."""

import pytest

from app.repositories.sql.budget_sql_repository import BudgetSqlRepository
from app.repositories.sql.user_sql_repository import UserSqlRepository


@pytest.fixture
def user_id(tmp_sqlite_path):
    return UserSqlRepository(db_path=tmp_sqlite_path).create(
        name="Sebastian", email="seba@example.com", password_hash="h"
    )["id"]


def test_create_devuelve_dict_con_user_name(tmp_sqlite_path, user_id):
    repo = BudgetSqlRepository(db_path=tmp_sqlite_path)
    created = repo.create(user_id, "daily", 50000)
    assert created["amount"] == 50000
    assert created["type"] == "daily"
    assert created["user_name"] == "Sebastian"
    assert created["enabled"] == 1


def test_get_by_user_and_type(tmp_sqlite_path, user_id):
    repo = BudgetSqlRepository(db_path=tmp_sqlite_path)
    repo.create(user_id, "weekly", 100000)
    found = repo.get_by_user_and_type(user_id, "weekly")
    assert found is not None
    assert found["amount"] == 100000


def test_get_enabled_by_user_solo_habilitados(tmp_sqlite_path, user_id):
    repo = BudgetSqlRepository(db_path=tmp_sqlite_path)
    b1 = repo.create(user_id, "daily", 10000)
    b2 = repo.create(user_id, "monthly", 200000)
    repo.update(b2["id"], enabled=False)

    enabled = repo.get_enabled_by_user(user_id)
    assert len(enabled) == 1
    assert enabled[0]["id"] == b1["id"]


def test_update_modifica_campos_no_nulos(tmp_sqlite_path, user_id):
    repo = BudgetSqlRepository(db_path=tmp_sqlite_path)
    created = repo.create(user_id, "daily", 50000)
    updated = repo.update(created["id"], amount=75000)
    assert updated["amount"] == 75000
    assert updated["type"] == "daily"


def test_delete_elimina(tmp_sqlite_path, user_id):
    repo = BudgetSqlRepository(db_path=tmp_sqlite_path)
    created = repo.create(user_id, "daily", 50000)
    assert repo.delete(created["id"]) is True
    assert repo.get_by_id(created["id"]) is None
