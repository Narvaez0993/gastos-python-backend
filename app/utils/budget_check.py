
from __future__ import annotations

from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.utils.dates import get_period_range

def check_budgets(
    budget_repo: IBudgetRepository,
    expense_repo: IExpenseRepository,
    user_id: int,
    tz: str = "America/Bogota",
) -> list[dict]:
    budgets = budget_repo.get_enabled_by_user(user_id)
    alerts: list[dict] = []

    for budget in budgets:
        start, end = get_period_range(budget["type"], None, None, tz)
        if start is None or end is None:
            continue

        spent = expense_repo.get_spent_in_period(
            user_id, start.isoformat(), end.isoformat()
        )

        if budget["amount"] <= 0:
            continue

        percentage = round((spent / budget["amount"]) * 100)
        if percentage >= 80:
            alerts.append(
                {
                    "type": budget["type"],
                    "limit": budget["amount"],
                    "spent": spent,
                    "remaining": budget["amount"] - spent,
                    "percentage": percentage,
                }
            )

    return alerts
