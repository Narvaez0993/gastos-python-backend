"""Interfaces (ABCs) que definen los contratos de la capa de persistencia.

Estos puertos siguen el patrón Repository y permiten que la capa de servicio
dependa de abstracciones, no de implementaciones concretas (principio DIP / SOLID).
"""

from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.user_repository import IUserRepository

__all__ = [
    "IBudgetRepository",
    "IExpenseRepository",
    "IMoneySourceMovementRepository",
    "IMoneySourceRepository",
    "IUserRepository",
]
