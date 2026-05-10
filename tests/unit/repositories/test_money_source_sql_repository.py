"""Pruebas unitarias del repositorio SQL crudo de fuentes de dinero."""

import pytest

from app.repositories.sql.money_source_sql_repository import MoneySourceSqlRepository
from app.repositories.sql.person_sql_repository import PersonSqlRepository


@pytest.fixture
def person_id(tmp_sqlite_path):
    person = PersonSqlRepository(db_path=tmp_sqlite_path).create("Sebastian")
    return person["id"]


def test_create_con_balance_inicial(tmp_sqlite_path, person_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    result = repo.create(person_id, "Nequi", "nequi", balance=100000)
    assert result["balance"] == 100000
    assert result["name"] == "Nequi"
    assert result["enabled"] == 1


def test_get_by_person_filtra_correctamente(tmp_sqlite_path, person_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    repo.create(person_id, "Nequi", "nequi", balance=10000)
    repo.create(person_id, "Bancolombia", "bancolombia", balance=50000)

    other_person = PersonSqlRepository(db_path=tmp_sqlite_path).create("Otra")
    repo.create(other_person["id"], "OtroNequi", "otronequi", balance=999)

    sources = repo.get_by_person(person_id)
    assert len(sources) == 2
    names = sorted(s["name"] for s in sources)
    assert names == ["Bancolombia", "Nequi"]


def test_check_duplicate_name_detecta_duplicado(tmp_sqlite_path, person_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    repo.create(person_id, "Nequi", "nequi")
    assert repo.check_duplicate_name(person_id, "nequi") is True
    assert repo.check_duplicate_name(person_id, "otronombre") is False


def test_check_duplicate_name_excluye_id(tmp_sqlite_path, person_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    source = repo.create(person_id, "Nequi", "nequi")
    assert repo.check_duplicate_name(person_id, "nequi", exclude_id=source["id"]) is False


def test_update_balance_persiste_cambio(tmp_sqlite_path, person_id):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    source = repo.create(person_id, "Nequi", "nequi", balance=100)
    assert repo.update_balance(source["id"], 250.5) is True
    assert repo.get_by_id(source["id"])["balance"] == 250.5


def test_get_by_person_and_normalized_name_devuelve_none_si_no_existe(
    tmp_sqlite_path, person_id
):
    repo = MoneySourceSqlRepository(db_path=tmp_sqlite_path)
    assert repo.get_by_person_and_normalized_name(person_id, "no-existe") is None
