from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MoneySourceCreate(BaseModel):
    personName: str
    name: str
    balance: float = 0


class MoneySourceOut(BaseModel):
    id: int
    person_id: int
    name: str
    name_normalized: str
    balance: float
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MoneySourceUpdate(BaseModel):
    balance: float | None = None
    enabled: bool | None = None
    name: str | None = None


class DepositRequest(BaseModel):
    amount: float
    note: str | None = None
    date: str | None = None
