"""Implementaciones de repositorios usando SQLAlchemy ORM (equivalente Python de JPA)."""

from app.repositories.jpa.money_source_jpa_repository import MoneySourceJpaRepository
from app.repositories.jpa.person_jpa_repository import PersonJpaRepository

__all__ = ["MoneySourceJpaRepository", "PersonJpaRepository"]
