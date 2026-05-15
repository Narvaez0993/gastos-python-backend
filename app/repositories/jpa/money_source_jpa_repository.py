"""Implementación JPA (SQLAlchemy ORM) del repositorio de fuentes de dinero."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.money_source_model import MoneySource
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository


class MoneySourceJpaRepository(IMoneySourceRepository):
    """Repositorio de fuentes de dinero usando SQLAlchemy ORM."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_dict(ms: MoneySource) -> dict:
        return {
            "id": ms.id,
            "user_id": ms.user_id,
            "name": ms.name,
            "name_normalized": ms.name_normalized,
            "balance": ms.balance,
            "enabled": ms.enabled,
            "created_at": ms.created_at,
        }

    def get_all(self) -> list[dict]:
        stmt = select(MoneySource).order_by(
            MoneySource.enabled.desc(), MoneySource.name.asc()
        )
        return [self._to_dict(ms) for ms in self.db.execute(stmt).scalars().all()]

    def get_by_id(self, source_id: int) -> Optional[dict]:
        ms = self.db.get(MoneySource, source_id)
        return self._to_dict(ms) if ms else None

    def get_by_user(self, user_id: int) -> list[dict]:
        stmt = (
            select(MoneySource)
            .where(MoneySource.user_id == user_id)
            .order_by(MoneySource.enabled.desc(), MoneySource.name.asc())
        )
        return [self._to_dict(ms) for ms in self.db.execute(stmt).scalars().all()]

    def get_by_user_and_normalized_name(
        self, user_id: int, name_normalized: str
    ) -> Optional[dict]:
        stmt = select(MoneySource).where(
            MoneySource.user_id == user_id,
            MoneySource.name_normalized == name_normalized,
        )
        ms = self.db.execute(stmt).scalar_one_or_none()
        return self._to_dict(ms) if ms else None

    def create(
        self,
        user_id: int,
        name: str,
        name_normalized: str,
        balance: float = 0,
    ) -> dict:
        ms = MoneySource(
            user_id=user_id,
            name=name,
            name_normalized=name_normalized,
            balance=balance,
        )
        self.db.add(ms)
        self.db.commit()
        self.db.refresh(ms)
        return self._to_dict(ms)

    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        name_normalized: Optional[str] = None,
        balance: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[dict]:
        ms = self.db.get(MoneySource, source_id)
        if not ms:
            return None

        if name is not None:
            ms.name = name
        if name_normalized is not None:
            ms.name_normalized = name_normalized
        if balance is not None:
            ms.balance = balance
        if enabled is not None:
            ms.enabled = 1 if enabled else 0

        self.db.commit()
        self.db.refresh(ms)
        return self._to_dict(ms)

    def update_balance(self, source_id: int, new_balance: float) -> bool:
        ms = self.db.get(MoneySource, source_id)
        if not ms:
            return False
        ms.balance = new_balance
        self.db.commit()
        return True

    def delete(self, source_id: int) -> bool:
        ms = self.db.get(MoneySource, source_id)
        if not ms:
            return False
        self.db.delete(ms)
        self.db.commit()
        return True

    def check_duplicate_name(
        self,
        user_id: int,
        name_normalized: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        stmt = select(MoneySource.id).where(
            MoneySource.user_id == user_id,
            MoneySource.name_normalized == name_normalized,
        )
        if exclude_id:
            stmt = stmt.where(MoneySource.id != exclude_id)
        return self.db.execute(stmt).first() is not None
