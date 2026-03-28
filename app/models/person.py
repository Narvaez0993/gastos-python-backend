from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    expenses: Mapped[list["Expense"]] = relationship(back_populates="person")  # noqa: F821
    money_sources: Mapped[list["MoneySource"]] = relationship(back_populates="person")  # noqa: F821
    budgets: Mapped[list["Budget"]] = relationship(back_populates="person")  # noqa: F821
