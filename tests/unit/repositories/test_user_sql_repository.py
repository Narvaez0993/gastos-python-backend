from app.repositories.sql.user_sql_repository import UserSqlRepository


def _repo(db_path):
    return UserSqlRepository(db_path=db_path)


def _create(repo, name="Sebastian", email="seba@example.com", password_hash="h"):
    return repo.create(name=name, email=email, password_hash=password_hash)


def test_create_devuelve_user_sin_password_hash(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    result = _create(repo)
    assert set(result.keys()) == {"id", "name", "email", "created_at"}
    assert result["name"] == "Sebastian"
    assert result["email"] == "seba@example.com"


def test_get_by_id_inexistente_devuelve_none(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    assert repo.get_by_id(999) is None


def test_get_all_ordenado_alfabeticamente(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    _create(repo, name="Carlos", email="c@e.com")
    _create(repo, name="Ana", email="a@e.com")
    _create(repo, name="Beto", email="b@e.com")
    nombres = [u["name"] for u in repo.get_all()]
    assert nombres == ["Ana", "Beto", "Carlos"]


def test_get_by_email_inexistente_devuelve_none(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    assert repo.get_by_email("nadie@nope.com") is None


def test_get_by_email_devuelve_user_sin_password_hash(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    _create(repo, email="findme@e.com")
    found = repo.get_by_email("findme@e.com")
    assert found is not None
    assert "password_hash" not in found
    assert found["email"] == "findme@e.com"


def test_get_by_email_with_credentials_incluye_password_hash(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    _create(repo, email="creds@e.com", password_hash="$bcrypt$xxxx")
    found = repo.get_by_email_with_credentials("creds@e.com")
    assert found is not None
    assert found["password_hash"] == "$bcrypt$xxxx"


def test_update_name_modifica_solo_nombre(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = _create(repo)
    updated = repo.update_name(created["id"], "Cambiado")
    assert updated["name"] == "Cambiado"
    assert updated["email"] == created["email"]


def test_update_email_modifica_solo_email(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = _create(repo, email="old@e.com")
    updated = repo.update_email(created["id"], "new@e.com")
    assert updated["email"] == "new@e.com"
    assert updated["name"] == created["name"]


def test_update_password_hash_devuelve_true_si_user_existe(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = _create(repo)
    assert repo.update_password_hash(created["id"], "newhash") is True
    assert repo.update_password_hash(999, "x") is False


def test_delete_devuelve_true_si_existe(tmp_sqlite_path):
    repo = _repo(tmp_sqlite_path)
    created = _create(repo)
    assert repo.delete(created["id"]) is True
    assert repo.delete(created["id"]) is False
    assert repo.get_by_id(created["id"]) is None
