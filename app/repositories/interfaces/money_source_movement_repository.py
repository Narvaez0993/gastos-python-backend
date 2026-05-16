
from abc import ABC, abstractmethod
from typing import Optional

class IMoneySourceMovementRepository(ABC):

    @abstractmethod
    def get_by_source(self, source_id: int) -> list[dict]:
        pass

    @abstractmethod
    def create(
        self,
        money_source_id: int,
        movement_type: str,
        amount: float,
        balance_before: float,
        balance_after: float,
        date: str,
        expense_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    def has_movements(self, source_id: int) -> bool:
        pass

    @abstractmethod
    def get_filtered(
        self,
        source_id: int,
        movement_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        pass
