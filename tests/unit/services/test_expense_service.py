"""Pruebas unitarias de ExpenseService con mocks de los 4 repositorios."""

import pytest
from fastapi import HTTPException

from app.schemas.expense import ExpenseCreate
from app.services.expense_service import ExpenseService


def _service(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_budget_repo.get_enabled_by_user.return_value = []
    return ExpenseService(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )


def test_create_con_money_source_decrementa_balance(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 7, "user_id": 1, "name": "Nequi",
        "name_normalized": "nequi", "balance": 1000,
        "enabled": 1, "created_at": "x",
    }
    mock_expense_repo.create.return_value = {
        "id": 100, "user_id": 1, "amount": 200,
        "description": "Almuerzo", "category": None,
        "date": "2026-05-09T12:00:00+00:00",
        "money_source_id": 7, "created_at": "x",
    }
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )
    data = ExpenseCreate(
        amount=200, description="Almuerzo",
        date="2026-05-09", money_source_id=7,
    )

    result = service.create_expense(user_id=1, data=data)

    mock_money_source_repo.update_balance.assert_called_once_with(7, 800)
    assert result["expense"]["amount"] == 200


def test_create_lanza_404_si_money_source_no_pertenece_al_user(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 7, "user_id": 2, "name": "OtraFuente",
        "name_normalized": "otra", "balance": 1000,
        "enabled": 1, "created_at": "x",
    }
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )
    data = ExpenseCreate(
        amount=200, description="X", date="2026-05-09", money_source_id=7,
    )
    with pytest.raises(HTTPException) as exc:
        service.create_expense(user_id=1, data=data)
    assert exc.value.status_code == 404


def test_create_lanza_400_si_money_source_deshabilitada(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 7, "user_id": 1, "name": "Nequi",
        "name_normalized": "nequi", "balance": 1000,
        "enabled": 0, "created_at": "x",
    }
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )
    data = ExpenseCreate(
        amount=200, description="Almuerzo",
        date="2026-05-09", money_source_id=7,
    )
    with pytest.raises(HTTPException) as exc:
        service.create_expense(user_id=1, data=data)
    assert exc.value.status_code == 400
    mock_expense_repo.create.assert_not_called()


def test_delete_revierte_balance_si_tenia_money_source(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_expense_repo.get_by_id.return_value = {
        "id": 100, "user_id": 1, "amount": 200,
        "description": "X", "category": None,
        "date": "x", "money_source_id": 7, "created_at": "x",
    }
    mock_money_source_repo.get_by_id.return_value = {
        "id": 7, "user_id": 1, "name": "Nequi",
        "name_normalized": "nequi", "balance": 800,
        "enabled": 1, "created_at": "x",
    }
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )

    service.delete_expense(100, user_id=1)

    # Balance se revierte: 800 + 200 = 1000
    mock_money_source_repo.update_balance.assert_called_once_with(7, 1000)
    mock_expense_repo.delete.assert_called_once_with(100)


def test_delete_lanza_404_si_no_es_del_user(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_expense_repo.get_by_id.return_value = {
        "id": 100, "user_id": 2, "amount": 200, "money_source_id": None,
        "description": "X", "category": None, "date": "x", "created_at": "x",
    }
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )
    with pytest.raises(HTTPException) as exc:
        service.delete_expense(100, user_id=1)
    assert exc.value.status_code == 404
    mock_expense_repo.delete.assert_not_called()


def test_get_summary_delega_a_repo(
    mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
):
    mock_expense_repo.get_summary.return_value = {"total": 0, "by_category": []}
    service = _service(
        mock_expense_repo, mock_money_source_repo, mock_movement_repo, mock_budget_repo
    )

    result = service.get_summary(user_id=1)

    mock_expense_repo.get_summary.assert_called_once()
    assert result == {"total": 0, "by_category": []}
