from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseImage(Base):
    __tablename__ = "expense_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)

    expense: Mapped["Expense"] = relationship(back_populates="images")  # noqa: F821
