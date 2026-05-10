"""Wiring de inyección de dependencias para FastAPI.

Aquí se decide qué implementación concreta de cada repositorio se usa
(SQL crudo o JPA / SQLAlchemy) según los settings, y se construyen los
services pasándoles sus repositorios. Las routes consumen estas factory
functions vía Depends().
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.session import get_db
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.person_repository import IPersonRepository
from app.repositories.jpa import MoneySourceJpaRepository, PersonJpaRepository
from app.repositories.sql import (
    BudgetSqlRepository,
    ExpenseSqlRepository,
    MoneySourceMovementSqlRepository,
    MoneySourceSqlRepository,
    PersonSqlRepository,
)
from app.services.budget_service import BudgetService
from app.services.expense_service import ExpenseService
from app.services.money_source_service import MoneySourceService
from app.services.person_service import PersonService

# ---- Repositorios ----
# Persons y MoneySources tienen dos backends seleccionables (SQL crudo o JPA / SQLAlchemy ORM).
# Expenses, Budgets y Movements usan solo SQL crudo, pero igual dependen de su interfaz para
# que los services no estén acoplados a la implementación concreta (DIP).


def get_person_repo(db: Session = Depends(get_db)) -> IPersonRepository:
    if get_settings().PERSON_REPO_BACKEND == "jpa":
        return PersonJpaRepository(db)
    return PersonSqlRepository()


def get_money_source_repo(db: Session = Depends(get_db)) -> IMoneySourceRepository:
    if get_settings().MONEY_SOURCE_REPO_BACKEND == "jpa":
        return MoneySourceJpaRepository(db)
    return MoneySourceSqlRepository()


def get_expense_repo() -> IExpenseRepository:
    return ExpenseSqlRepository()


def get_budget_repo() -> IBudgetRepository:
    return BudgetSqlRepository()


def get_movement_repo() -> IMoneySourceMovementRepository:
    return MoneySourceMovementSqlRepository()


# ---- Services ----


def get_person_service(
    person_repo: IPersonRepository = Depends(get_person_repo),
) -> PersonService:
    return PersonService(person_repo)


def get_money_source_service(
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    person_repo: IPersonRepository = Depends(get_person_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
) -> MoneySourceService:
    return MoneySourceService(money_source_repo, person_repo, movement_repo)


def get_budget_service(
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
    person_repo: IPersonRepository = Depends(get_person_repo),
) -> BudgetService:
    return BudgetService(budget_repo, person_repo)


def get_expense_service(
    expense_repo: IExpenseRepository = Depends(get_expense_repo),
    person_repo: IPersonRepository = Depends(get_person_repo),
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
) -> ExpenseService:
    return ExpenseService(
        expense_repo, person_repo, money_source_repo, movement_repo, budget_repo
    )
