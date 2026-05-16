from fastapi import HTTPException

from app.repositories.interfaces.budget_repository import IBudgetRepository

def _format_budget(row):
    return {
        "id": row["id"],
        "user": {"id": row["user_id"], "name": row["user_name"]},
        "type": row["type"],
        "amount": row["amount"],
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"],
    }

class BudgetService:

    def __init__(self, budget_repo: IBudgetRepository):
        self.budget_repo = budget_repo

    def list_budgets(self, user_id):
        rows = self.budget_repo.get_by_user(user_id)
        return [_format_budget(row) for row in rows]

    def get_budget(self, budget_id, user_id):
        row = self.budget_repo.get_by_id(budget_id)
        if not row or row["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        return _format_budget(row)

    def create_or_update_budget(self, user_id, data):
        if not data.type or not data.amount:
            raise HTTPException(
                status_code=400,
                detail="type y amount son requeridos",
            )

        if data.type not in ("daily", "weekly", "monthly"):
            raise HTTPException(
                status_code=400,
                detail="type debe ser daily, weekly o monthly",
            )

        existing = self.budget_repo.get_by_user_and_type(user_id, data.type)

        if existing:
            updated = self.budget_repo.update(existing["id"], amount=data.amount, enabled=True)
            return {
                "id": updated["id"],
                "user_id": updated["user_id"],
                "type": updated["type"],
                "amount": updated["amount"],
                "enabled": bool(updated["enabled"]),
                "created_at": updated["created_at"],
            }

        created = self.budget_repo.create(user_id, data.type, data.amount)
        return {
            "id": created["id"],
            "user_id": created["user_id"],
            "type": created["type"],
            "amount": created["amount"],
            "enabled": bool(created["enabled"]),
            "created_at": created["created_at"],
        }

    def update_budget(self, budget_id, user_id, data):
        existing = self.budget_repo.get_by_id(budget_id)
        if not existing or existing["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        if data.type and data.type not in ("daily", "weekly", "monthly"):
            raise HTTPException(
                status_code=400,
                detail="type debe ser daily, weekly o monthly",
            )

        updated = self.budget_repo.update(
            budget_id,
            amount=data.amount,
            enabled=data.enabled,
            budget_type=data.type,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        return _format_budget(updated)

    def delete_budget(self, budget_id, user_id):
        existing = self.budget_repo.get_by_id(budget_id)
        if not existing or existing["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        self.budget_repo.delete(budget_id)
        return {"message": "Presupuesto eliminado"}
