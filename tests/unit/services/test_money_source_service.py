import pytest
from fastapi import HTTPException

from app.schemas.money_source import DepositRequest, MoneySourceCreate
from app.services.money_source_service import MoneySourceService


def _service(mock_money_source_repo, mock_movement_repo):
    return MoneySourceService(mock_money_source_repo, mock_movement_repo)


def test_create_lanza_409_si_nombre_duplicado(
    mock_money_source_repo, mock_movement_repo
):
    mock_money_source_repo.check_duplicate_name.return_value = True
    service = _service(mock_money_source_repo, mock_movement_repo)

    with pytest.raises(HTTPException) as exc:
        service.create_money_source(user_id=1, data=MoneySourceCreate(name="Nequi"))
    assert exc.value.status_code == 409


def test_create_con_balance_inicial_crea_movimiento_adjustment(
    mock_money_source_repo, mock_movement_repo
):
    mock_money_source_repo.check_duplicate_name.return_value = False
    mock_money_source_repo.create.return_value = {
        "id": 5, "user_id": 1, "name": "Nequi",
        "name_normalized": "nequi", "balance": 100, "enabled": 1, "created_at": "x",
    }
    service = _service(mock_money_source_repo, mock_movement_repo)

    service.create_money_source(
        user_id=1, data=MoneySourceCreate(name="Nequi", balance=100)
    )

    mock_movement_repo.create.assert_called_once()
    kwargs = mock_movement_repo.create.call_args.kwargs
    assert kwargs["movement_type"] == "adjustment"
    assert kwargs["balance_after"] == 100


def test_deposit_actualiza_balance_y_crea_movimiento(
    mock_money_source_repo, mock_movement_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 1, "user_id": 1, "name": "Nequi",
        "name_normalized": "nequi", "balance": 100,
        "enabled": 1, "created_at": "x",
    }
    mock_movement_repo.create.return_value = {
        "id": 2, "money_source_id": 1, "type": "deposit",
        "amount": 50, "balance_before": 100, "balance_after": 150,
        "expense_id": None, "note": None, "date": "x", "created_at": "x",
        "expense_description": None, "expense_amount": None, "expense_category": None,
    }
    service = _service(mock_money_source_repo, mock_movement_repo)

    service.deposit(1, user_id=1, data=DepositRequest(amount=50))

    mock_money_source_repo.update_balance.assert_called_once_with(1, 150)


def test_deposit_lanza_404_si_no_es_del_user(
    mock_money_source_repo, mock_movement_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 1, "user_id": 2, "name": "Nequi",
        "name_normalized": "nequi", "balance": 100,
        "enabled": 1, "created_at": "x",
    }
    service = _service(mock_money_source_repo, mock_movement_repo)
    with pytest.raises(HTTPException) as exc:
        service.deposit(1, user_id=1, data=DepositRequest(amount=50))
    assert exc.value.status_code == 404


def test_delete_lanza_400_si_tiene_movimientos(
    mock_money_source_repo, mock_movement_repo
):
    mock_money_source_repo.get_by_id.return_value = {
        "id": 1, "user_id": 1, "balance": 0, "enabled": 1,
    }
    mock_movement_repo.has_movements.return_value = True
    service = _service(mock_money_source_repo, mock_movement_repo)

    with pytest.raises(HTTPException) as exc:
        service.delete_money_source(1, user_id=1)
    assert exc.value.status_code == 400
    mock_money_source_repo.delete.assert_not_called()
