from fastapi import HTTPException

from app.dao.budget_dao import BudgetDAO
from app.dao.person_dao import PersonDAO


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

    @staticmethod
    def list_budgets(person_id):
        if not person_id:
            raise HTTPException(
                status_code=400, detail="El parámetro personId es requerido"
            )

        rows = BudgetDAO.get_by_person(person_id)
        return [_format_budget(row) for row in rows]

    @staticmethod
    def get_budget(budget_id):
        row = BudgetDAO.get_by_id(budget_id)
        if not row:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        return _format_budget(row)

    @staticmethod
    def create_or_update_budget(data):
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

        person = PersonDAO.get_by_id(data.person_id)
        if not person:
            raise HTTPException(
                status_code=404,
                detail=f"Persona con id {data.person_id} no encontrada",
            )

        existing = BudgetDAO.get_by_person_and_type(data.person_id, data.type)

        if existing:
            updated = BudgetDAO.update(existing["id"], amount=data.amount, enabled=True)
            return {
                "id": updated["id"],
                "person_id": updated["person_id"],
                "type": updated["type"],
                "amount": updated["amount"],
                "enabled": bool(updated["enabled"]),
                "created_at": updated["created_at"],
            }

        created = BudgetDAO.create(data.person_id, data.type, data.amount)
        return {
            "id": created["id"],
            "person_id": created["person_id"],
            "type": created["type"],
            "amount": created["amount"],
            "enabled": bool(created["enabled"]),
            "created_at": created["created_at"],
        }

    @staticmethod
    def update_budget(budget_id, data):
        existing = BudgetDAO.get_by_id(budget_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        if data.type and data.type not in ("daily", "weekly", "monthly"):
            raise HTTPException(
                status_code=400,
                detail="type debe ser daily, weekly o monthly",
            )

        updated = BudgetDAO.update(
            budget_id,
            amount=data.amount,
            enabled=data.enabled,
            budget_type=data.type,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        return _format_budget(updated)

    @staticmethod
    def delete_budget(budget_id):
        existing = BudgetDAO.get_by_id(budget_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

        BudgetDAO.delete(budget_id)
        return {"message": "Presupuesto eliminado"}
