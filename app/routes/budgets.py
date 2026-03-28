from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers import budget_controller
from app.database import get_db
from app.schemas.budget import BudgetCreate

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.post("/", status_code=201)
def create_or_update_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    """Create or update a budget (upsert by person + type)."""
    budget = budget_controller.create_or_update_budget(db, data)
    return {
        "id": budget.id,
        "person_id": budget.person_id,
        "type": budget.type,
        "amount": budget.amount,
        "enabled": budget.enabled,
        "created_at": budget.created_at,
    }


@router.get("/")
def list_budgets(personName: str = Query(...), db: Session = Depends(get_db)):
    """List budgets for a person."""
    return budget_controller.list_budgets(db, personName)


@router.delete("/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget."""
    return budget_controller.delete_budget(db, budget_id)
