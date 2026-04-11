from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.dao.money_source_dao import MoneySourceDAO
from app.dao.money_source_movement_dao import MoneySourceMovementDAO
from app.dao.person_dao import PersonDAO


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

    @staticmethod
    def list_money_sources(person_id):
        if not person_id:
            raise HTTPException(
                status_code=400, detail="El parámetro personId es requerido"
            )

        return MoneySourceDAO.get_by_person(person_id)

    @staticmethod
    def get_money_source(source_id):
        source = MoneySourceDAO.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")
        return source

    @staticmethod
    def create_money_source(data):
        if not data.person_id or not data.name:
            raise HTTPException(
                status_code=400, detail="person_id y name son requeridos"
            )

        person = PersonDAO.get_by_id(data.person_id)
        if not person:
            raise HTTPException(
                status_code=404,
                detail=f"Persona con id {data.person_id} no encontrada",
            )

        name = data.name.strip()
        name_normalized = name.lower().strip()

        if MoneySourceDAO.check_duplicate_name(data.person_id, name_normalized):
            raise HTTPException(
                status_code=409,
                detail=f'Ya tienes una fuente de dinero llamada "{data.name}"',
            )

        source = MoneySourceDAO.create(
            data.person_id, name, name_normalized, data.balance
        )

        if data.balance and data.balance != 0:
            MoneySourceMovementDAO.create(
                money_source_id=source["id"],
                movement_type="adjustment",
                amount=abs(data.balance),
                balance_before=0,
                balance_after=data.balance,
                note="Balance inicial",
                date=datetime.now(timezone.utc).isoformat(),
            )

        return source

    @staticmethod
    def update_money_source(source_id, data):
        source = MoneySourceDAO.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if data.balance is not None and data.balance != source["balance"]:
            balance_before = source["balance"]
            balance_after = data.balance
            MoneySourceDAO.update_balance(source_id, balance_after)

            MoneySourceMovementDAO.create(
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
            if MoneySourceDAO.check_duplicate_name(
                source["person_id"], new_normalized, exclude_id=source_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Ya tienes una fuente de dinero con ese nombre",
                )

        updated = MoneySourceDAO.update(
            source_id,
            name=data.name.strip() if data.name is not None else None,
            name_normalized=data.name.strip().lower() if data.name is not None else None,
            balance=data.balance,
            enabled=data.enabled,
        )
        return updated

    @staticmethod
    def delete_money_source(source_id):
        source = MoneySourceDAO.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if MoneySourceMovementDAO.has_movements(source_id):
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar una fuente de dinero con movimientos. Deshabilítala en su lugar.",
            )

        MoneySourceDAO.delete(source_id)
        return {"message": "Fuente de dinero eliminada"}

    @staticmethod
    def deposit(source_id, data):
        if not data.amount or data.amount <= 0:
            raise HTTPException(
                status_code=400, detail="Se requiere un monto positivo"
            )

        source = MoneySourceDAO.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if not source["enabled"]:
            raise HTTPException(
                status_code=400,
                detail="No se puede depositar en una fuente de dinero deshabilitada",
            )

        balance_before = source["balance"]
        balance_after = balance_before + data.amount
        MoneySourceDAO.update_balance(source_id, balance_after)

        deposit_date = datetime.now(timezone.utc).isoformat()
        if data.date:
            try:
                parsed = datetime.strptime(data.date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                deposit_date = parsed.isoformat()
            except ValueError:
                deposit_date = datetime.now(timezone.utc).isoformat()

        movement = MoneySourceMovementDAO.create(
            money_source_id=source_id,
            movement_type="deposit",
            amount=data.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=data.note,
            date=deposit_date,
        )

        updated_source = MoneySourceDAO.get_by_id(source_id)

        return {
            "movement": _format_movement(movement),
            "source": updated_source,
        }

    @staticmethod
    def get_movements(source_id, movement_type=None, start_date=None,
                      end_date=None, page=1, limit=20):
        source = MoneySourceDAO.get_by_id(source_id)
        if not source:
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

        result = MoneySourceMovementDAO.get_filtered(
            source_id, movement_type, sd, ed, page, limit
        )

        result["movements"] = [_format_movement(m) for m in result["movements"]]
        return result
