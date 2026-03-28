from datetime import datetime

from pydantic import BaseModel


class BudgetCreate(BaseModel):
    personName: str
    type: str
    amount: float


class BudgetPersonOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class BudgetOut(BaseModel):
    id: int
    person: BudgetPersonOut
    type: str
    amount: float
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetCreatedOut(BaseModel):
    id: int
    person_id: int
    type: str
    amount: float
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
