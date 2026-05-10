"""Pruebas unitarias del repositorio SQL crudo de gastos."""

import pytest

from app.repositories.sql.expense_sql_repository import ExpenseSqlRepository
from app.repositories.sql.person_sql_repository import PersonSqlRepository


@pytest.fixture
def person_id(tmp_sqlite_path):
    return PersonSqlRepository(db_path=tmp_sqlite_path).create("Sebastian")["id"]


def test_create_y_get_by_id_devuelven_mismo_registro(tmp_sqlite_path, person_id):
    repo = ExpenseSqlRepository(db_path=tmp_sqlite_path)
    created = repo.create(person_id, 25000, "Almuerzo", "Comida", "2026-05-09T12:00:00+00:00")
    fetched = repo.get_by_id(created["id"])
    assert fetched["id"] == created["id"]
    assert fetched["amount"] == 25000
    assert fetched["person_name"] == "Sebastian"


def test_get_filtered_por_persona_y_rango(tmp_sqlite_path, person_id):
    repo = ExpenseSqlRepository(db_path=tmp_sqlite_path)
    repo.create(person_id, 1000, "G1", None, "2026-05-01T12:00:00+00:00")
    repo.create(person_id, 2000, "G2", None, "2026-05-15T12:00:00+00:00")

    results = repo.get_filtered(
        person_id=person_id,
        start_date="2026-05-10T00:00:00+00:00",
        end_date="2026-05-31T23:59:59+00:00",
    )
    assert len(results) == 1
    assert results[0]["amount"] == 2000


def test_get_summary_agrupa_por_categoria(tmp_sqlite_path, person_id):
    repo = ExpenseSqlRepository(db_path=tmp_sqlite_path)
    repo.create(person_id, 1000, "G1", "Comida", "2026-05-01T12:00:00+00:00")
    repo.create(person_id, 500, "G2", "Comida", "2026-05-02T12:00:00+00:00")
    repo.create(person_id, 200, "G3", "Transporte", "2026-05-03T12:00:00+00:00")

    summary = repo.get_summary(person_id=person_id)
    assert summary["total"] == 1700
    cats = {c["category"]: c["total"] for c in summary["by_category"]}
    assert cats["Comida"] == 1500
    assert cats["Transporte"] == 200


def test_delete_elimina_y_devuelve_bool(tmp_sqlite_path, person_id):
    repo = ExpenseSqlRepository(db_path=tmp_sqlite_path)
    created = repo.create(person_id, 100, "X", None, "2026-05-09T12:00:00+00:00")
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.get_by_id(created["id"]) is None
