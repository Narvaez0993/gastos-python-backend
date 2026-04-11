from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.dao.expense_dao import ExpenseDAO
from app.dao.money_source_dao import MoneySourceDAO
from app.dao.money_source_movement_dao import MoneySourceMovementDAO
from app.dao.person_dao import PersonDAO
from app.utils.budget_check import check_budgets, get_period_range, parse_date_to_noon_utc


def resolve_tz(tz_query: str | None, tz_header: str | None) -> str:
    return tz_query or tz_header or "America/Bogota"


def _format_expense(row):
    """Formatea una fila de la BD al formato de respuesta de la API."""
    ms = None
    if row.get("ms_id"):
        ms = {
            "id": row["ms_id"],
            "name": row["ms_name"],
            "balance": row["ms_balance"],
            "enabled": bool(row["ms_enabled"]),
        }
    return {
        "id": row["id"],
        "person": {"id": row["person_id"], "name": row["person_name"]},
        "amount": row["amount"],
        "description": row["description"],
        "category": row["category"],
        "date": row["date"],
        "money_source": ms,
        "created_at": row["created_at"],
    }


class ExpenseService:

    @staticmethod
    def list_expenses(person_id=None, period=None, start_date=None,
                      end_date=None, tz="America/Bogota"):
        range_start, range_end = get_period_range(period, start_date, end_date, tz)
        start_str = range_start.isoformat() if range_start else None
        end_str = range_end.isoformat() if range_end else None

        rows = ExpenseDAO.get_filtered(person_id, start_str, end_str)
        return [_format_expense(row) for row in rows]

    @staticmethod
    def get_expense(expense_id):
        row = ExpenseDAO.get_by_id(expense_id)
        if not row:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
        return _format_expense(row)

    @staticmethod
    def create_expense(data, tz="America/Bogota"):
        if not data.person_id or not data.amount or not data.description or not data.date:
            raise HTTPException(
                status_code=400,
                detail="person_id, amount, description y date son requeridos",
            )

        person = PersonDAO.get_by_id(data.person_id)
        if not person:
            raise HTTPException(
                status_code=404,
                detail=f"Persona con id {data.person_id} no encontrada",
            )

        source = None
        if data.money_source_id:
            source = MoneySourceDAO.get_by_id(data.money_source_id)
            if not source or source["person_id"] != person["id"]:
                raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if source and not source["enabled"]:
            raise HTTPException(
                status_code=400,
                detail=f'La fuente de dinero "{source["name"]}" está deshabilitada',
            )

        expense_date = parse_date_to_noon_utc(data.date)
        expense_date_str = expense_date.isoformat()

        expense = ExpenseDAO.create(
            person_id=person["id"],
            amount=float(data.amount),
            description=data.description.strip(),
            category=data.category.strip() if data.category else None,
            date=expense_date_str,
            money_source_id=source["id"] if source else None,
        )

        money_source_info = None
        if source:
            balance_before = source["balance"]
            balance_after = balance_before - float(data.amount)
            MoneySourceDAO.update_balance(source["id"], balance_after)

            MoneySourceMovementDAO.create(
                money_source_id=source["id"],
                movement_type="expense",
                amount=float(data.amount),
                balance_before=balance_before,
                balance_after=balance_after,
                expense_id=expense["id"],
                date=expense_date_str,
            )

            money_source_info = {
                "name": source["name"],
                "balance_before": balance_before,
                "amount_deducted": float(data.amount),
                "balance_after": balance_after,
            }
            if balance_after < 0:
                money_source_info["warning"] = "El balance quedó en negativo"

        budget_alerts = check_budgets(person["id"], tz)

        return {
            "expense": {
                "id": expense["id"],
                "person_id": expense["person_id"],
                "amount": expense["amount"],
                "description": expense["description"],
                "category": expense["category"],
                "date": expense["date"],
                "money_source_id": expense["money_source_id"],
                "created_at": expense["created_at"],
            },
            "budget_alerts": budget_alerts,
            "money_source": money_source_info,
        }

    @staticmethod
    def update_expense(expense_id, data):
        existing = ExpenseDAO.get_by_id(expense_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        expense_date = parse_date_to_noon_utc(data.date)
        expense_date_str = expense_date.isoformat()

        updated = ExpenseDAO.update(
            expense_id=expense_id,
            amount=float(data.amount),
            description=data.description.strip(),
            category=data.category.strip() if data.category else None,
            date=expense_date_str,
            money_source_id=data.money_source_id,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        return _format_expense(updated)

    @staticmethod
    def delete_expense(expense_id):
        existing = ExpenseDAO.get_by_id(expense_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        if existing["money_source_id"]:
            source = MoneySourceDAO.get_by_id(existing["money_source_id"])
            if source:
                balance_before = source["balance"]
                balance_after = balance_before + existing["amount"]
                MoneySourceDAO.update_balance(source["id"], balance_after)

                MoneySourceMovementDAO.create(
                    money_source_id=source["id"],
                    movement_type="adjustment",
                    amount=existing["amount"],
                    balance_before=balance_before,
                    balance_after=balance_after,
                    note="Gasto eliminado — balance revertido",
                    date=datetime.now(timezone.utc).isoformat(),
                )

        ExpenseDAO.delete(expense_id)
        return {"message": "Gasto eliminado"}

    @staticmethod
    def get_summary(person_id=None, period=None, start_date=None,
                    end_date=None, tz="America/Bogota"):
        range_start, range_end = get_period_range(period, start_date, end_date, tz)
        start_str = range_start.isoformat() if range_start else None
        end_str = range_end.isoformat() if range_end else None

        return ExpenseDAO.get_summary(person_id, start_str, end_str)
