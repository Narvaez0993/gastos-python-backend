"""Implementación JPA (SQLAlchemy ORM) del repositorio de personas."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.person_model import Person
from app.repositories.interfaces.person_repository import IPersonRepository


class PersonJpaRepository(IPersonRepository):
    """Repositorio de personas usando SQLAlchemy ORM.

    El shape de los dicts devueltos coincide con el del repositorio SQL crudo
    para que los services no necesiten saber qué backend está activo.
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_dict(person: Person) -> dict:
        return {
            "id": person.id,
            "name": person.name,
            "created_at": person.created_at,
        }

    def get_all(self) -> list[dict]:
        stmt = select(Person).order_by(Person.name.asc())
        return [self._to_dict(p) for p in self.db.execute(stmt).scalars().all()]

    def get_by_id(self, person_id: int) -> Optional[dict]:
        person = self.db.get(Person, person_id)
        return self._to_dict(person) if person else None

    def get_by_name(self, name: str) -> Optional[dict]:
        stmt = select(Person).where(Person.name == name)
        person = self.db.execute(stmt).scalar_one_or_none()
        return self._to_dict(person) if person else None

    def create(self, name: str) -> dict:
        person = Person(name=name)
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        return self._to_dict(person)

    def update(self, person_id: int, name: str) -> Optional[dict]:
        person = self.db.get(Person, person_id)
        if not person:
            return None
        person.name = name
        self.db.commit()
        self.db.refresh(person)
        return self._to_dict(person)

    def delete(self, person_id: int) -> bool:
        person = self.db.get(Person, person_id)
        if not person:
            return False
        try:
            self.db.delete(person)
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            return False
