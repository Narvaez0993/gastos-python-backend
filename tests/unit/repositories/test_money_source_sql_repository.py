"""Pruebas unitarias del repositorio SQL crudo de fuentes de dinero."""

import pytest

from app.repositories.sql.money_source_sql_repository import MoneySourceSqlRepository
from app.repositories.sql.user_sql_repository import UserSqlRepository


@pytest.fixture
def user_id(tmp_sqlite_path):
    user = UserSqlRepository(db_path=tmp_sqlite_path).create(
        name="Sebastian", email="seba@example.com", password_hash="h"
    )
    return user["id"]


def test_create_con_balance_inicial(tmp_sqlite_path, user_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    result = repo.create(user_id, "Nequi", "nequi", balance=100000)
    assert result["balance"] == 100000
    assert result["name"] == "Nequi"
    assert result["enabled"] == 1


def test_get_by_user_filtra_correctamente(tmp_sqlite_path, user_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    repo.create(user_id, "Nequi", "nequi", balance=10000)
    repo.create(user_id, "Bancolombia", "bancolombia", balance=50000)

    other_user = UserSqlRepository(db_path=tmp_sqlite_path).create(
        name="Otra", email="otra@example.com", password_hash="h"
    )
    repo.create(other_user["id"], "OtroNequi", "otronequi", balance=999)

    sources = repo.get_by_user(user_id)
    assert len(sources) == 2
    names = sorted(s["name"] for s in sources)
    assert names == ["Bancolombia", "Nequi"]


def test_check_duplicate_name_detecta_duplicado(tmp_sqlite_path, user_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    repo.create(user_id, "Nequi", "nequi")
    assert repo.check_duplicate_name(user_id, "nequi") is True
    assert repo.check_duplicate_name(user_id, "otronombre") is False


def test_check_duplicate_name_excluye_id(tmp_sqlite_path, user_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    source = repo.create(user_id, "Nequi", "nequi")
    assert repo.check_duplicate_name(user_id, "nequi", exclude_id=source["id"]) is False


def test_update_balance_persiste_cambio(tmp_sqlite_path, user_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    source = repo.create(user_id, "Nequi", "nequi", balance=100)
    assert repo.update_balance(source["id"], 250.5) is True
    assert repo.get_by_id(source["id"])["balance"] == 250.5


def test_get_by_user_and_normalized_name_devuelve_none_si_no_existe(
    tmp_sqlite_path, user_id
):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    assert repo.get_by_user_and_normalized_name(user_id, "no-existe") is None
