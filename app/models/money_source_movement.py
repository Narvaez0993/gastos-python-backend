from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MoneySourceMovement(Base):
    __tablename__ = "money_source_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    money_source_id: Mapped[int] = mapped_column(
        ForeignKey("money_sources.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)  # expense, deposit, adjustment
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_before: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    expense_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("expenses.id"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    money_source: Mapped["MoneySource"] = relationship(back_populates="movements")  # noqa: F821
    expense: Mapped["Optional[Expense]"] = relationship()  # noqa: F821
