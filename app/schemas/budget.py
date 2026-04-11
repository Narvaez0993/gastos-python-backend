from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class BudgetCreate(BaseModel):
    personName: str
    type: str
    amount: float


class BudgetUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    enabled: Optional[bool] = None


class BudgetPersonOut(BaseModel):
    id: int
    name: str


class BudgetOut(BaseModel):
    id: int
    person: BudgetPersonOut
    type: str
    amount: float
    enabled: bool
    created_at: str


class BudgetCreatedOut(BaseModel):
    id: int
    person_id: int
    type: str
    amount: float
    enabled: bool
    created_at: str
