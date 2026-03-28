from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.person import Person
from app.schemas.budget import BudgetCreate


def create_or_update_budget(db: Session, data: BudgetCreate) -> Budget:
    if not data.personName or not data.type or not data.amount:
        raise HTTPException(
            status_code=400,
            detail="personName, type, and amount are required",
        )

    if data.type not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=400,
            detail="type must be daily, weekly, or monthly",
        )

    person = db.query(Person).filter(Person.name == data.personName).first()
    if not person:
        raise HTTPException(
            status_code=404, detail=f'Person "{data.personName}" not found'
        )

    existing = (
        db.query(Budget)
        .filter(Budget.person_id == person.id, Budget.type == data.type)
        .first()
    )

    if existing:
        existing.amount = data.amount
        existing.enabled = True
        db.commit()
        db.refresh(existing)
        return existing

    budget = Budget(
        person_id=person.id,
        type=data.type,
        amount=data.amount,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def list_budgets(db: Session, person_name: str) -> list[dict]:
    if not person_name:
        raise HTTPException(
            status_code=400, detail="personName query param is required"
        )

    person = db.query(Person).filter(Person.name == person_name).first()
    if not person:
        return []

    budgets = db.query(Budget).filter(Budget.person_id == person.id).all()
    result = []
    for b in budgets:
        result.append(
            {
                "id": b.id,
                "person": {"id": person.id, "name": person.name},
                "type": b.type,
                "amount": b.amount,
                "enabled": b.enabled,
                "created_at": b.created_at,
            }
        )
    return result


def delete_budget(db: Session, budget_id: int) -> dict:
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted"}
