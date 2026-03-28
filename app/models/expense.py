from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(nullable=False)
    money_source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("money_sources.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    person: Mapped["Person"] = relationship(back_populates="expenses")  # noqa: F821
    money_source: Mapped["Optional[MoneySource]"] = relationship()  # noqa: F821
    images: Mapped[list["ExpenseImage"]] = relationship(  # noqa: F821
        back_populates="expense", cascade="all, delete-orphan"
    )
