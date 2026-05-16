
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.user_model import User
from app.repositories.interfaces.user_repository import IUserRepository

class UserJpaRepository(IUserRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_public_dict(user: User) -> dict:
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
        }

    @staticmethod
    def _to_credentials_dict(user: User) -> dict:
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password_hash": user.password_hash,
            "created_at": user.created_at,
        }

    def get_all(self) -> list[dict]:
        stmt = select(User).order_by(User.name.asc())
        return [self._to_public_dict(u) for u in self.db.execute(stmt).scalars().all()]

    def get_by_id(self, user_id: int) -> Optional[dict]:
        user = self.db.get(User, user_id)
        return self._to_public_dict(user) if user else None

    def get_by_email(self, email: str) -> Optional[dict]:
        stmt = select(User).where(User.email == email)
        user = self.db.execute(stmt).scalar_one_or_none()
        return self._to_public_dict(user) if user else None

    def get_by_email_with_credentials(self, email: str) -> Optional[dict]:
        stmt = select(User).where(User.email == email)
        user = self.db.execute(stmt).scalar_one_or_none()
        return self._to_credentials_dict(user) if user else None

    def create(self, name: str, email: str, password_hash: str) -> dict:
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_public_dict(user)

    def update_name(self, user_id: int, name: str) -> Optional[dict]:
        user = self.db.get(User, user_id)
        if not user:
            return None
        user.name = name
        self.db.commit()
        self.db.refresh(user)
        return self._to_public_dict(user)

    def update_email(self, user_id: int, email: str) -> Optional[dict]:
        user = self.db.get(User, user_id)
        if not user:
            return None
        user.email = email
        self.db.commit()
        self.db.refresh(user)
        return self._to_public_dict(user)

    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        user = self.db.get(User, user_id)
        if not user:
            return False
        user.password_hash = password_hash
        self.db.commit()
        return True

    def delete(self, user_id: int) -> bool:
        user = self.db.get(User, user_id)
        if not user:
            return False
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            return False
