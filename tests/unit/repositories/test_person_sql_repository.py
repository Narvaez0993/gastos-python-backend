"""Pruebas unitarias del repositorio SQL crudo de personas."""

from app.repositories.sql.person_sql_repository import PersonSqlRepository


def _repo(db_path):
    return PersonSqlRepository(db_path=db_path)


def test_create_persona_devuelve_id_y_nombre(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    result = repo.create("Sebastian")
    assert result["id"] is not None
    assert result["name"] == "Sebastian"
    assert "created_at" in result


def test_get_by_id_inexistente_devuelve_none(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    assert repo.get_by_id(999) is None


def test_get_all_ordenado_alfabeticamente(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    repo.create("Carlos")
    repo.create("Ana")
    repo.create("Beto")
    nombres = [p["name"] for p in repo.get_all()]
    assert nombres == ["Ana", "Beto", "Carlos"]


def test_update_modifica_nombre(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = repo.create("Original")
    updated = repo.update(created["id"], "Cambiado")
    assert updated["name"] == "Cambiado"
    assert updated["id"] == created["id"]


def test_delete_devuelve_true_si_existe_y_false_si_no(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = repo.create("Eliminable")
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.get_by_id(created["id"]) is None


def test_get_by_name_devuelve_none_si_no_existe(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    assert repo.get_by_name("NadieAsi") is None
    repo.create("Sebastian")
    found = repo.get_by_name("Sebastian")
    assert found is not None
    assert found["name"] == "Sebastian"
