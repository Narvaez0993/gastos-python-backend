"""Pruebas unitarias del repositorio JPA (SQLAlchemy) de personas."""

from app.repositories.jpa.person_jpa_repository import PersonJpaRepository


def test_create_devuelve_dict_con_shape_compatible_con_sql(db_session):
    repo = PersonJpaRepository(db_session)
    result = repo.create("Sebastian")
    assert set(result.keys()) == {"id", "name", "created_at"}
    assert result["name"] == "Sebastian"
    assert result["id"] is not None


def test_get_by_id_devuelve_none_si_no_existe(db_session):
    repo = PersonJpaRepository(db_session)
    assert repo.get_by_id(999) is None


def test_get_all_ordenado_alfabeticamente(db_session):
    repo = PersonJpaRepository(db_session)
    repo.create("Carlos")
    repo.create("Ana")
    repo.create("Beto")
    nombres = [p["name"] for p in repo.get_all()]
    assert nombres == ["Ana", "Beto", "Carlos"]


def test_update_modifica_y_devuelve_dict_actualizado(db_session):
    repo = PersonJpaRepository(db_session)
    created = repo.create("Original")
    updated = repo.update(created["id"], "Cambiado")
    assert updated["name"] == "Cambiado"
    assert updated["id"] == created["id"]


def test_delete_devuelve_bool(db_session):
    repo = PersonJpaRepository(db_session)
    created = repo.create("Eliminable")
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.get_by_id(created["id"]) is None
