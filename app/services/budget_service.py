from fastapi import HTTPException

from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.person_repository import IPersonRepository


def _format_budget(row):
    """Formatea una fila de la BD al formato de respuesta de la API."""
    return {
        "id": row["id"],
        "person": {"id": row["person_id"], "name": row["person_name"]},
        "type": row["type"],
        "amount": row["amount"],
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"],
    }


class BudgetService:
    """Lógica de negocio para presupuestos. Depende de IBudgetRepository e IPersonRepository."""

    def __init__(
        self,
        budget_repo: IBudgetRepository,
        person_repo: IPersonRepository,
    ):
        self.budget_repo = budget_repo
        self.person_repo = person_repo

    def list_budgets(self, person_id):
        if not person_id:
            raise HTTPException(
                status_code=400, detail="El parámetro personId es requerido"
            )

        rows = self.budget_repo.get_by_person(person_id)
        return [_format_budget(row) for row in rows]

    def get_budget(self, budget_id):
        row = self.budget_repo.get_by_id(budget_id)
        if not row:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        return _format_budget(row)

    def create_or_update_budget(self, data):
        if not data.person_id or not data.type or not data.amount:
            raise HTTPException(
                status_code=400,
                detail="person_id, type y amount son requeridos",
            )

        if data.type not in ("daily", "weekly", "monthly"):
            raise HTTPException(
                status_code=400,
                detail="type debe ser daily, weekly o monthly",
            )

        person = self.person_repo.get_by_id(data.person_id)
        if not person:
            raise HTTPException(
                status_code=404,
                detail=f"Persona con id {data.person_id} no encontrada",
            )

        existing = self.budget_repo.get_by_person_and_type(data.person_id, data.type)

        if existing:
            updated = self.budget_repo.update(existing["id"], amount=data.amount, enabled=True)
            return {
                "id": updated["id"],
                "person_id": updated["person_id"],
                "type": updated["type"],
                "amount": updated["amount"],
                "enabled": bool(updated["enabled"]),
                "created_at": updated["created_at"],
            }

        created = self.budget_repo.create(data.person_id, data.type, data.amount)
        return {
            "id": created["id"],
            "person_id": created["person_id"],
            "type": created["type"],
            "amount": created["amount"],
            "enabled": bool(created["enabled"]),
            "created_at": created["created_at"],
        }

    def update_budget(self, budget_id, data):
        existing = self.budget_repo.get_by_id(budget_id)
        if not existing:
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

    def delete_budget(self, budget_id):
        existing = self.budget_repo.get_by_id(budget_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        self.budget_repo.delete(budget_id)
        return {"message": "Presupuesto eliminado"}
