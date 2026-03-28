from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.person import Person
from app.schemas.person import PersonCreate


def create_person(db: Session, data: PersonCreate) -> Person:
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    person = Person(name=name)
    try:
        db.add(person)
        db.commit()
        db.refresh(person)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Person already exists")

    return person


def list_persons(db: Session) -> list[Person]:
    return db.query(Person).order_by(Person.name.asc()).all()
