from typing import Optional

from fastapi import APIRouter, Depends, Form, Header, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.controllers import expense_controller
from app.database import get_db

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("/", status_code=201)
async def create_expense(
    personName: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    category: Optional[str] = Form(None),
    moneySourceId: Optional[int] = Form(None),
    moneySourceName: Optional[str] = Form(None),
    images: list[UploadFile] = File(default=[]),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    db: Session = Depends(get_db),
):
    """Create a new expense with optional image uploads and money source."""
    resolved_tz = expense_controller.resolve_tz(tz, x_timezone)
    return await expense_controller.create_expense(
        db=db,
        person_name=personName,
        amount=amount,
        description=description,
        date_str=date,
        category=category,
        money_source_id=moneySourceId,
        money_source_name=moneySourceName,
        images=images if images else None,
        tz=resolved_tz,
    )


@router.get("/summary")
def get_summary(
    personName: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    db: Session = Depends(get_db),
):
    """Get expense summary grouped by category."""
    resolved_tz = expense_controller.resolve_tz(tz, x_timezone)
    return expense_controller.get_expense_summary(
        db, personName, period, startDate, endDate, resolved_tz
    )


@router.get("/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get a single expense by ID."""
    return expense_controller.get_expense(db, expense_id)


@router.get("/")
def list_expenses(
    personName: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    db: Session = Depends(get_db),
):
    """List expenses with optional filters."""
    resolved_tz = expense_controller.resolve_tz(tz, x_timezone)
    return expense_controller.list_expenses(
        db, personName, period, startDate, endDate, resolved_tz
    )


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete an expense. Reverts money source balance if applicable."""
    return expense_controller.delete_expense(db, expense_id)
