from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ExpensePersonOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ExpenseMoneySourceOut(BaseModel):
    id: int
    name: str
    balance: float
    enabled: bool
    model_config = {"from_attributes": True}


class ExpenseOut(BaseModel):
    id: int
    person: ExpensePersonOut
    amount: float
    description: str
    category: str | None
    date: datetime
    money_source: ExpenseMoneySourceOut | None = None
    images: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseCreatedOut(BaseModel):
    id: int
    person_id: int
    amount: float
    description: str
    category: str | None
    date: datetime
    money_source_id: int | None = None
    images: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class MoneySourceInfo(BaseModel):
    name: str
    balance_before: float
    amount_deducted: float
    balance_after: float
    warning: str | None = None


class BudgetAlert(BaseModel):
    type: str
    limit: float
    spent: float
    remaining: float
    percentage: float


class ExpenseCreateResponse(BaseModel):
    expense: ExpenseCreatedOut
    budget_alerts: list[BudgetAlert] = []
    money_source: MoneySourceInfo | None = None


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummaryOut(BaseModel):
    total: float
    by_category: list[CategorySummary]
