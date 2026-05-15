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
from app.repositories.interfaces.user_repository import IUserRepository
from app.repositories.jpa import MoneySourceJpaRepository, UserJpaRepository
from app.repositories.sql import (
    AttachmentSqlRepository,
    BudgetSqlRepository,
    ExpenseSqlRepository,
    MoneySourceMovementSqlRepository,
    MoneySourceSqlRepository,
    UserSqlRepository,
)
from app.services.ai_capture_service import AICaptureService
from app.services.attachment_service import AttachmentService
from app.services.auth_service import AuthService
from app.services.budget_service import BudgetService
from app.services.expense_service import ExpenseService
from app.services.money_source_service import MoneySourceService
from app.services.storage_service import LocalFilesystemBackend, StorageBackend

# ---- Repositorios ----
# Users y MoneySources tienen dos backends seleccionables (SQL crudo o JPA / SQLAlchemy ORM).
# Expenses, Budgets y Movements usan solo SQL crudo, pero igual dependen de su interfaz
# para que los services no estén acoplados a la implementación concreta (DIP).


def get_user_repo(db: Session = Depends(get_db)) -> IUserRepository:
    if get_settings().USER_REPO_BACKEND == "jpa":
        return UserJpaRepository(db)
    return UserSqlRepository()


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


def get_auth_service(
    user_repo: IUserRepository = Depends(get_user_repo),
) -> AuthService:
    return AuthService(user_repo)


def get_money_source_service(
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
) -> MoneySourceService:
    return MoneySourceService(money_source_repo, movement_repo)


def get_budget_service(
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
) -> BudgetService:
    return BudgetService(budget_repo)


def get_attachment_repo_eager() -> AttachmentSqlRepository:
    return AttachmentSqlRepository()


def get_expense_service(
    expense_repo: IExpenseRepository = Depends(get_expense_repo),
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
    attachment_repo: AttachmentSqlRepository = Depends(get_attachment_repo_eager),
) -> ExpenseService:
    return ExpenseService(
        expense_repo, money_source_repo, movement_repo, budget_repo, attachment_repo
    )


def get_ai_capture_service(
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
) -> AICaptureService:
    return AICaptureService(get_settings(), money_source_repo)


def get_attachment_repo() -> AttachmentSqlRepository:
    return AttachmentSqlRepository()


def get_storage_backend() -> StorageBackend:
    return LocalFilesystemBackend(get_settings())


def get_attachment_service(
    repo: AttachmentSqlRepository = Depends(get_attachment_repo),
    storage: StorageBackend = Depends(get_storage_backend),
    ai: AICaptureService = Depends(get_ai_capture_service),
) -> AttachmentService:
    return AttachmentService(get_settings(), storage, repo, ai)
