"""Pruebas unitarias del repositorio JPA (SQLAlchemy) de fuentes de dinero."""

import pytest

from app.repositories.jpa.money_source_jpa_repository import MoneySourceJpaRepository
from app.repositories.jpa.person_jpa_repository import PersonJpaRepository


@pytest.fixture
def person_id(db_session):
    return PersonJpaRepository(db_session).create("Sebastian")["id"]


def test_create_devuelve_dict_con_shape_compatible(db_session, person_id):
    repo = MoneySourceJpaRepository(db_session)
    result = repo.create(person_id, "Nequi", "nequi", balance=100000)
    assert set(result.keys()) == {
        "id", "person_id", "name", "name_normalized",
        "balance", "enabled", "created_at",
    }
    assert result["balance"] == 100000
    assert result["enabled"] == 1


def test_get_by_person_devuelve_solo_de_esa_persona(db_session, person_id):
    repo = MoneySourceJpaRepository(db_session)
    repo.create(person_id, "Nequi", "nequi", balance=10000)
    repo.create(person_id, "Bancolombia", "bancolombia", balance=50000)

    other_person_id = PersonJpaRepository(db_session).create("Otra")["id"]
    repo.create(other_person_id, "OtroNequi", "otronequi", balance=999)

    sources = repo.get_by_person(person_id)
    assert len(sources) == 2


def test_check_duplicate_name_detecta_y_excluye(db_session, person_id):
    repo = MoneySourceJpaRepository(db_session)
    source = repo.create(person_id, "Nequi", "nequi")
    assert repo.check_duplicate_name(person_id, "nequi") is True
    assert repo.check_duplicate_name(person_id, "otro") is False
    assert repo.check_duplicate_name(person_id, "nequi", exclude_id=source["id"]) is False


def test_update_balance_persiste(db_session, person_id):
    repo = MoneySourceJpaRepository(db_session)
    source = repo.create(person_id, "Nequi", "nequi", balance=100)
    assert repo.update_balance(source["id"], 250.5) is True
    assert repo.get_by_id(source["id"])["balance"] == 250.5


def test_delete_remueve_y_devuelve_bool(db_session, person_id):
    repo = MoneySourceJpaRepository(db_session)
    source = repo.create(person_id, "Nequi", "nequi")
    assert repo.delete(source["id"]) is True
    assert repo.get_by_id(source["id"]) is None
