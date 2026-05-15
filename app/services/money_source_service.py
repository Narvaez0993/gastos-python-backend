from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository


def _format_movement(row):
    """Formatea un movimiento de la BD al formato de respuesta."""
    expense_data = None
    if row.get("expense_id") and row.get("expense_description"):
        expense_data = {
            "id": row["expense_id"],
            "description": row["expense_description"],
            "amount": row["expense_amount"],
            "category": row["expense_category"],
        }
    return {
        "id": row["id"],
        "money_source_id": row["money_source_id"],
        "type": row["type"],
        "amount": row["amount"],
        "balance_before": row["balance_before"],
        "balance_after": row["balance_after"],
        "expense": expense_data,
        "note": row["note"],
        "date": row["date"],
        "created_at": row["created_at"],
    }


class MoneySourceService:
    """Lógica de negocio para fuentes de dinero. El user_id viene del JWT."""

    def __init__(
        self,
        money_source_repo: IMoneySourceRepository,
        movement_repo: IMoneySourceMovementRepository,
    ):
        self.money_source_repo = money_source_repo
        self.movement_repo = movement_repo

    def list_money_sources(self, user_id):
        return self.money_source_repo.get_by_user(user_id)

    def get_money_source(self, source_id, user_id):
        source = self.money_source_repo.get_by_id(source_id)
        if not source or source["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")
        return source

    def create_money_source(self, user_id, data):
        if not data.name:
            raise HTTPException(status_code=400, detail="name es requerido")

        name = data.name.strip()
        name_normalized = name.lower().strip()

        if self.money_source_repo.check_duplicate_name(user_id, name_normalized):
            raise HTTPException(
                status_code=409,
                detail=f'Ya tienes una fuente de dinero llamada "{data.name}"',
            )

        source = self.money_source_repo.create(
            user_id, name, name_normalized, data.balance
        )

        if data.balance and data.balance != 0:
            self.movement_repo.create(
                money_source_id=source["id"],
                movement_type="adjustment",
                amount=abs(data.balance),
                balance_before=0,
                balance_after=data.balance,
                note="Balance inicial",
                date=datetime.now(timezone.utc).isoformat(),
            )

        return source

    def update_money_source(self, source_id, user_id, data):
        source = self.money_source_repo.get_by_id(source_id)
        if not source or source["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if data.balance is not None and data.balance != source["balance"]:
            balance_before = source["balance"]
            balance_after = data.balance
            self.money_source_repo.update_balance(source_id, balance_after)

            self.movement_repo.create(
                money_source_id=source_id,
                movement_type="adjustment",
                amount=abs(balance_after - balance_before),
                balance_before=balance_before,
                balance_after=balance_after,
                note="Ajuste manual",
                date=datetime.now(timezone.utc).isoformat(),
            )

        if data.name is not None:
            new_name = data.name.strip()
            new_normalized = new_name.lower().strip()
            if self.money_source_repo.check_duplicate_name(
                user_id, new_normalized, exclude_id=source_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Ya tienes una fuente de dinero con ese nombre",
                )

        updated = self.money_source_repo.update(
            source_id,
            name=data.name.strip() if data.name is not None else None,
            name_normalized=data.name.strip().lower() if data.name is not None else None,
            balance=data.balance,
            enabled=data.enabled,
        )
        return updated

    def delete_money_source(self, source_id, user_id):
        source = self.money_source_repo.get_by_id(source_id)
        if not source or source["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if self.movement_repo.has_movements(source_id):
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar una fuente de dinero con movimientos. Deshabilítala en su lugar.",
            )

        self.money_source_repo.delete(source_id)
        return {"message": "Fuente de dinero eliminada"}

    def deposit(self, source_id, user_id, data):
        if not data.amount or data.amount <= 0:
            raise HTTPException(
                status_code=400, detail="Se requiere un monto positivo"
            )

        source = self.money_source_repo.get_by_id(source_id)
        if not source or source["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if not source["enabled"]:
            raise HTTPException(
                status_code=400,
                detail="No se puede depositar en una fuente de dinero deshabilitada",
            )

        balance_before = source["balance"]
        balance_after = balance_before + data.amount
        self.money_source_repo.update_balance(source_id, balance_after)

        deposit_date = datetime.now(timezone.utc).isoformat()
        if data.date:
            try:
                parsed = datetime.strptime(data.date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                deposit_date = parsed.isoformat()
            except ValueError:
                deposit_date = datetime.now(timezone.utc).isoformat()

        movement = self.movement_repo.create(
            money_source_id=source_id,
            movement_type="deposit",
            amount=data.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=data.note,
            date=deposit_date,
        )

        updated_source = self.money_source_repo.get_by_id(source_id)

        return {
            "movement": _format_movement(movement),
            "source": updated_source,
        }

    def get_movements(
        self, source_id, user_id, movement_type=None, start_date=None,
        end_date=None, page=1, limit=20,
    ):
        source = self.money_source_repo.get_by_id(source_id)
        if not source or source["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        sd = None
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                ).isoformat()
            except ValueError:
                pass

        ed = None
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999000,
                    tzinfo=timezone.utc
                ).isoformat()
            except ValueError:
                pass

        result = self.movement_repo.get_filtered(
            source_id, movement_type, sd, ed, page, limit
        )

        result["movements"] = [_format_movement(m) for m in result["movements"]]
        return result
