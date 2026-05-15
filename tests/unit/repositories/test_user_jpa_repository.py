"""Pruebas unitarias del repositorio JPA (SQLAlchemy) de usuarios."""

from app.repositories.jpa.user_jpa_repository import UserJpaRepository


def _create(repo, name="Sebastian", email="seba@example.com", password_hash="h"):
    return repo.create(name=name, email=email, password_hash=password_hash)


def test_create_devuelve_dict_sin_password_hash(db_session):
    repo = UserJpaRepository(db_session)
    result = _create(repo)
    assert set(result.keys()) == {"id", "name", "email", "created_at"}
    assert result["name"] == "Sebastian"


def test_get_by_email_with_credentials_incluye_password_hash(db_session):
    repo = UserJpaRepository(db_session)
    _create(repo, email="creds@e.com", password_hash="$bcrypt$x")
    found = repo.get_by_email_with_credentials("creds@e.com")
    assert found is not None
    assert found["password_hash"] == "$bcrypt$x"


def test_get_by_email_omite_password_hash(db_session):
    repo = UserJpaRepository(db_session)
    _create(repo, email="pub@e.com", password_hash="$bcrypt$x")
    found = repo.get_by_email("pub@e.com")
    assert found is not None
    assert "password_hash" not in found


def test_get_all_ordenado_alfabeticamente(db_session):
    repo = UserJpaRepository(db_session)
    _create(repo, name="Carlos", email="c@e.com")
    _create(repo, name="Ana", email="a@e.com")
    _create(repo, name="Beto", email="b@e.com")
    assert [u["name"] for u in repo.get_all()] == ["Ana", "Beto", "Carlos"]


def test_update_name_modifica_solo_nombre(db_session):
    repo = UserJpaRepository(db_session)
    created = _create(repo)
    updated = repo.update_name(created["id"], "Cambiado")
    assert updated["name"] == "Cambiado"
    assert updated["email"] == created["email"]


def test_update_password_hash_devuelve_true_si_existe(db_session):
    repo = UserJpaRepository(db_session)
    created = _create(repo)
    assert repo.update_password_hash(created["id"], "newhash") is True
    assert repo.update_password_hash(999, "x") is False


def test_delete_devuelve_bool(db_session):
    repo = UserJpaRepository(db_session)
    created = _create(repo)
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.get_by_id(created["id"]) is None
