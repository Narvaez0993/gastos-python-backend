from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MoneySourceCreate(BaseModel):
    person_id: int
    name: str
    balance: float = 0


class MoneySourceUpdate(BaseModel):
    balance: Optional[float] = None
    enabled: Optional[bool] = None
    name: Optional[str] = None


class MoneySourceOut(BaseModel):
    id: int
    person_id: int
    name: str
    name_normalized: str
    balance: float
    enabled: bool
    created_at: str


class DepositRequest(BaseModel):
    amount: float
    note: Optional[str] = None
    date: Optional[str] = None
