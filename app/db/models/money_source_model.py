"""Modelo ORM MoneySource mapeado a la tabla money_sources."""

from sqlalchemy import Float, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MoneySource(Base):
    """Mapeo ORM de la tabla money_sources (creada por SQL crudo en init_db).

    Nota: enabled se mantiene como int (0/1) para mantener paridad de shape
    con los dicts que devuelve el repositorio SQL crudo.
    """

    __tablename__ = "money_sources"
    __table_args__ = (
        UniqueConstraint("person_id", "name_normalized", name="uq_person_name_normalized"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("persons.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    balance: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )
    enabled: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("(datetime('now'))")
    )
