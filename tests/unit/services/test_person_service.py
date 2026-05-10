"""Pruebas unitarias de PersonService con mocks de IPersonRepository."""

import pytest
from fastapi import HTTPException

from app.schemas.person import PersonCreate, PersonUpdate
from app.services.person_service import PersonService


def test_list_persons_delega_a_repo(mock_person_repo):
    mock_person_repo.get_all.return_value = [
        {"id": 1, "name": "Sebastian", "created_at": "2026-01-01"},
    ]
    service = PersonService(mock_person_repo)
    result = service.list_persons()
    mock_person_repo.get_all.assert_called_once()
    assert len(result) == 1


def test_get_person_lanza_404_si_no_existe(mock_person_repo):
    mock_person_repo.get_by_id.return_value = None
    service = PersonService(mock_person_repo)
    with pytest.raises(HTTPException) as exc:
        service.get_person(999)
    assert exc.value.status_code == 404


def test_create_person_lanza_409_si_nombre_duplicado(mock_person_repo):
    mock_person_repo.get_by_name.return_value = {
        "id": 1, "name": "Sebastian", "created_at": "..."
    }
    service = PersonService(mock_person_repo)
    with pytest.raises(HTTPException) as exc:
        service.create_person(PersonCreate(name="Sebastian"))
    assert exc.value.status_code == 409


def test_create_person_lanza_400_si_nombre_vacio(mock_person_repo):
    service = PersonService(mock_person_repo)
    with pytest.raises(HTTPException) as exc:
        service.create_person(PersonCreate(name="   "))
    assert exc.value.status_code == 400
    mock_person_repo.create.assert_not_called()


def test_delete_person_lanza_404_si_no_existe(mock_person_repo):
    mock_person_repo.get_by_id.return_value = None
    service = PersonService(mock_person_repo)
    with pytest.raises(HTTPException) as exc:
        service.delete_person(999)
    assert exc.value.status_code == 404
    mock_person_repo.delete.assert_not_called()
