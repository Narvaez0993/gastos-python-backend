from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MovementExpenseOut(BaseModel):
    id: int
    description: str
    amount: float
    category: Optional[str]


class MovementOut(BaseModel):
    id: int
    money_source_id: int
    type: str
    amount: float
    balance_before: float
    balance_after: float
    expense: Optional[MovementExpenseOut] = None
    note: Optional[str]
    date: str
    created_at: str


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
    source: MoneySourceOut


from app.schemas.money_source import MoneySourceOut  # noqa: E402

DepositResponse.model_rebuild()
