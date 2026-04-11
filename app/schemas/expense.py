from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    person_id: int
    amount: float
    description: str
    date: str
    category: Optional[str] = None
    money_source_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    amount: float
    description: str
    date: str
    category: Optional[str] = None
    money_source_id: Optional[int] = None


class ExpensePersonOut(BaseModel):
    id: int
    name: str


class ExpenseMoneySourceOut(BaseModel):
    id: int
    name: str
    balance: float
    enabled: bool


class ExpenseOut(BaseModel):
    id: int
    person: ExpensePersonOut
    amount: float
    description: str
    category: Optional[str]
    date: str
    money_source: Optional[ExpenseMoneySourceOut] = None
    created_at: str


class ExpenseCreatedOut(BaseModel):
    id: int
    person_id: int
    amount: float
    description: str
    category: Optional[str]
    date: str
    money_source_id: Optional[int] = None
    created_at: str


class MoneySourceInfo(BaseModel):
    name: str
    balance_before: float
    amount_deducted: float
    balance_after: float
    warning: Optional[str] = None


class BudgetAlert(BaseModel):
    type: str
    limit: float
    spent: float
    remaining: float
    percentage: float


class ExpenseCreateResponse(BaseModel):
    expense: ExpenseCreatedOut
    budget_alerts: list[BudgetAlert] = []
    money_source: Optional[MoneySourceInfo] = None


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummaryOut(BaseModel):
    total: float
    by_category: list[CategorySummary]
