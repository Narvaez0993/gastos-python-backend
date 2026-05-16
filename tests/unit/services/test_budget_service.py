import pytest
from fastapi import HTTPException

from app.schemas.budget import BudgetCreate
from app.services.budget_service import BudgetService


def _service(mock_budget_repo):
    return BudgetService(mock_budget_repo)


def test_create_o_update_lanza_400_si_type_invalido(mock_budget_repo):
    service = _service(mock_budget_repo)
    data = BudgetCreate(type="quincenal", amount=100)
    with pytest.raises(HTTPException) as exc:
        service.create_or_update_budget(user_id=1, data=data)
    assert exc.value.status_code == 400


def test_create_o_update_actualiza_si_existe_mismo_tipo(mock_budget_repo):
    mock_budget_repo.get_by_user_and_type.return_value = {
        "id": 7, "user_id": 1, "type": "daily",
        "amount": 50, "enabled": 1, "created_at": "x",
    }
    mock_budget_repo.update.return_value = {
        "id": 7, "user_id": 1, "type": "daily",
        "amount": 100, "enabled": 1, "created_at": "x",
    }
    service = _service(mock_budget_repo)

    result = service.create_or_update_budget(
        user_id=1, data=BudgetCreate(type="daily", amount=100)
    )

    mock_budget_repo.update.assert_called_once()
    mock_budget_repo.create.assert_not_called()
    assert result["amount"] == 100


def test_create_o_update_crea_si_no_existe(mock_budget_repo):
    mock_budget_repo.get_by_user_and_type.return_value = None
    mock_budget_repo.create.return_value = {
        "id": 9, "user_id": 1, "type": "weekly",
        "amount": 200, "enabled": 1, "created_at": "x",
    }
    service = _service(mock_budget_repo)

    result = service.create_or_update_budget(
        user_id=1, data=BudgetCreate(type="weekly", amount=200)
    )

    mock_budget_repo.create.assert_called_once_with(1, "weekly", 200)
    assert result["id"] == 9


def test_delete_lanza_404_si_no_existe(mock_budget_repo):
    mock_budget_repo.get_by_id.return_value = None
    service = _service(mock_budget_repo)
    with pytest.raises(HTTPException) as exc:
        service.delete_budget(999, user_id=1)
    assert exc.value.status_code == 404
    mock_budget_repo.delete.assert_not_called()


def test_delete_lanza_404_si_no_pertenece_al_user(mock_budget_repo):
    mock_budget_repo.get_by_id.return_value = {
        "id": 7, "user_id": 2, "type": "daily",
        "amount": 50, "enabled": 1, "created_at": "x",
    }
    service = _service(mock_budget_repo)
    with pytest.raises(HTTPException) as exc:
        service.delete_budget(7, user_id=1)
    assert exc.value.status_code == 404
    mock_budget_repo.delete.assert_not_called()
