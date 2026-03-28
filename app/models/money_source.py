from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MoneySource(Base):
    __tablename__ = "money_sources"
    __table_args__ = (
        UniqueConstraint("person_id", "name_normalized", name="uq_person_name_norm"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    name_normalized: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    person: Mapped["Person"] = relationship(back_populates="money_sources")  # noqa: F821
    movements: Mapped[list["MoneySourceMovement"]] = relationship(  # noqa: F821
        back_populates="money_source"
    )
