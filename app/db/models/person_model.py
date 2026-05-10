"""Modelo ORM Person mapeado a la tabla persons."""

from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Person(Base):
    """Mapeo ORM de la tabla persons (creada por SQL crudo en init_db)."""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("(datetime('now'))")
    )
