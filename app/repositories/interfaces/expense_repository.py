
from abc import ABC, abstractmethod
from typing import Optional

class IExpenseRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[dict]:
        pass

    @abstractmethod
    def get_by_id(self, expense_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    def create(
        self,
        user_id: int,
        amount: float,
        description: str,
        category: Optional[str],
        date: str,
        money_source_id: Optional[int] = None,
    ) -> dict:
        pass

    @abstractmethod
    def update(
        self,
        expense_id: int,
        amount: float,
        description: str,
        category: Optional[str],
        date: str,
        money_source_id: Optional[int] = None,
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def delete(self, expense_id: int) -> bool:
        pass

    @abstractmethod
    def get_filtered(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        pass

    @abstractmethod
    def get_summary(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    def get_spent_in_period(
        self, user_id: int, start_date: str, end_date: str
    ) -> float:
        pass
