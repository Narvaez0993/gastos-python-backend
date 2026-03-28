from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers import money_source_controller
from app.database import get_db
from app.schemas.money_source import (
    DepositRequest,
    MoneySourceCreate,
    MoneySourceOut,
    MoneySourceUpdate,
)

router = APIRouter(prefix="/api/money-sources", tags=["Money Sources"])


@router.post("/", response_model=MoneySourceOut, status_code=201)
def create_money_source(data: MoneySourceCreate, db: Session = Depends(get_db)):
    """Create a new money source with optional initial balance."""
    return money_source_controller.create_money_source(db, data)


@router.get("/", response_model=list[MoneySourceOut])
def list_money_sources(
    personName: str = Query(...), db: Session = Depends(get_db)
):
    """List money sources for a person, sorted by enabled then name."""
    return money_source_controller.list_money_sources(db, personName)


@router.patch("/{source_id}", response_model=MoneySourceOut)
def update_money_source(
    source_id: int, data: MoneySourceUpdate, db: Session = Depends(get_db)
):
    """Update money source balance, name, or enabled status."""
    return money_source_controller.update_money_source(db, source_id, data)


@router.delete("/{source_id}")
def delete_money_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a money source (only if it has no movements)."""
    return money_source_controller.delete_money_source(db, source_id)


@router.post("/{source_id}/deposit", status_code=201)
def deposit(source_id: int, data: DepositRequest, db: Session = Depends(get_db)):
    """Register a deposit/income to a money source."""
    result = money_source_controller.deposit(db, source_id, data)
    mov = result["movement"]
    src = result["source"]
    return {
        "movement": {
            "id": mov.id,
            "money_source_id": mov.money_source_id,
            "type": mov.type,
            "amount": mov.amount,
            "balance_before": mov.balance_before,
            "balance_after": mov.balance_after,
            "expense": None,
            "note": mov.note,
            "date": mov.date,
            "created_at": mov.created_at,
        },
        "source": {
            "id": src.id,
            "person_id": src.person_id,
            "name": src.name,
            "name_normalized": src.name_normalized,
            "balance": src.balance,
            "enabled": src.enabled,
            "created_at": src.created_at,
        },
    }


@router.get("/{source_id}/movements")
def get_movements(
    source_id: int,
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
    db: Session = Depends(get_db),
):
    """Get movement history with pagination and filters."""
    return money_source_controller.get_movements(
        db, source_id, type, startDate, endDate, page, limit
    )
