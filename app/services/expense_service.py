from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.sql.attachment_sql_repository import AttachmentSqlRepository
from app.utils.budget_check import check_budgets
from app.utils.dates import get_period_range, parse_date_to_noon_utc

def resolve_tz(tz_query: str | None, tz_header: str | None) -> str:
    return tz_query or tz_header or "America/Bogota"

def _format_expense(row):
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
        "user": {"id": row["user_id"], "name": row["user_name"]},
        "amount": row["amount"],
        "description": row["description"],
        "category": row["category"],
        "date": row["date"],
        "money_source": ms,
        "created_at": row["created_at"],
    }

class ExpenseService:

    def __init__(
        self,
        expense_repo: IExpenseRepository,
        money_source_repo: IMoneySourceRepository,
        movement_repo: IMoneySourceMovementRepository,
        budget_repo: IBudgetRepository,
        attachment_repo: AttachmentSqlRepository | None = None,
    ):
        self.expense_repo = expense_repo
        self.money_source_repo = money_source_repo
        self.movement_repo = movement_repo
        self.budget_repo = budget_repo
        self.attachment_repo = attachment_repo

    def list_expenses(self, user_id, period=None, start_date=None,
                      end_date=None, tz="America/Bogota"):
        range_start, range_end = get_period_range(period, start_date, end_date, tz)
        start_str = range_start.isoformat() if range_start else None
        end_str = range_end.isoformat() if range_end else None

        rows = self.expense_repo.get_filtered(user_id, start_str, end_str)
        return [_format_expense(row) for row in rows]

    def get_expense(self, expense_id, user_id):
        row = self.expense_repo.get_by_id(expense_id)
        if not row or row["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
        return _format_expense(row)

    def create_expense(self, user_id, data, tz="America/Bogota"):
        if not data.amount or not data.description or not data.date:
            raise HTTPException(
                status_code=400,
                detail="amount, description y date son requeridos",
            )

        source = None
        if data.money_source_id:
            source = self.money_source_repo.get_by_id(data.money_source_id)
            if not source or source["user_id"] != user_id:
                raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        if source and not source["enabled"]:
            raise HTTPException(
                status_code=400,
                detail=f'La fuente de dinero "{source["name"]}" está deshabilitada',
            )

        expense_date = parse_date_to_noon_utc(data.date)
        expense_date_str = expense_date.isoformat()

        expense = self.expense_repo.create(
            user_id=user_id,
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
            self.money_source_repo.update_balance(source["id"], balance_after)

            self.movement_repo.create(
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

        if data.attachment_ids and self.attachment_repo is not None:
            for att_id in data.attachment_ids:
                att = self.attachment_repo.get_by_id(att_id)
                if att and att["user_id"] == user_id and att["expense_id"] is None:
                    self.attachment_repo.link_to_expense(att_id, expense["id"])

        budget_alerts = check_budgets(
            self.budget_repo, self.expense_repo, user_id, tz
        )

        return {
            "expense": {
                "id": expense["id"],
                "user_id": expense["user_id"],
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

    def update_expense(self, expense_id, user_id, data):
        existing = self.expense_repo.get_by_id(expense_id)
        if not existing or existing["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        if data.money_source_id is not None:
            source = self.money_source_repo.get_by_id(data.money_source_id)
            if not source or source["user_id"] != user_id:
                raise HTTPException(status_code=404, detail="Fuente de dinero no encontrada")

        expense_date = parse_date_to_noon_utc(data.date)
        expense_date_str = expense_date.isoformat()

        updated = self.expense_repo.update(
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

    def delete_expense(self, expense_id, user_id):
        existing = self.expense_repo.get_by_id(expense_id)
        if not existing or existing["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        if existing["money_source_id"]:
            source = self.money_source_repo.get_by_id(existing["money_source_id"])
            if source:
                balance_before = source["balance"]
                balance_after = balance_before + existing["amount"]
                self.money_source_repo.update_balance(source["id"], balance_after)

                self.movement_repo.create(
                    money_source_id=source["id"],
                    movement_type="adjustment",
                    amount=existing["amount"],
                    balance_before=balance_before,
                    balance_after=balance_after,
                    note="Gasto eliminado — balance revertido",
                    date=datetime.now(timezone.utc).isoformat(),
                )

        self.expense_repo.delete(expense_id)
        return {"message": "Gasto eliminado"}

    def get_summary(self, user_id, period=None, start_date=None,
                    end_date=None, tz="America/Bogota"):
        range_start, range_end = get_period_range(period, start_date, end_date, tz)
        start_str = range_start.isoformat() if range_start else None
        end_str = range_end.isoformat() if range_end else None

        return self.expense_repo.get_summary(user_id, start_str, end_str)
