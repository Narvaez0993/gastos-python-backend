from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

class BudgetCreate(BaseModel):
    type: str
    amount: float

class BudgetUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    enabled: Optional[bool] = None

class BudgetUserOut(BaseModel):
    id: int
    name: str

class BudgetOut(BaseModel):
    id: int
    user: BudgetUserOut
    type: str
    amount: float
    enabled: bool
    created_at: str

class BudgetCreatedOut(BaseModel):
    id: int
    user_id: int
    type: str
    amount: float
    enabled: bool
    created_at: str
