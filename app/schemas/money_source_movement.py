from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MovementExpenseOut(BaseModel):
    id: int
    description: str
    amount: float
    category: str | None

    model_config = {"from_attributes": True}


class MovementOut(BaseModel):
    id: int
    money_source_id: int
    type: str
    amount: float
    balance_before: float
    balance_after: float
    expense: MovementExpenseOut | None = None
    note: str | None
    date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginationOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class MovementsListOut(BaseModel):
    movements: list[MovementOut]
    pagination: PaginationOut


class DepositResponse(BaseModel):
    movement: MovementOut
    source: "MoneySourceOut"  # noqa: F821

    model_config = {"from_attributes": True}


from app.schemas.money_source import MoneySourceOut  # noqa: E402

DepositResponse.model_rebuild()
