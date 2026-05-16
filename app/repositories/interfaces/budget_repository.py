
from abc import ABC, abstractmethod
from typing import Optional

class IBudgetRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[dict]:
        pass

    @abstractmethod
    def get_by_id(self, budget_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: int) -> list[dict]:
        pass

    @abstractmethod
    def get_by_user_and_type(
        self, user_id: int, budget_type: str
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def get_enabled_by_user(self, user_id: int) -> list[dict]:
        pass

    @abstractmethod
    def create(
        self, user_id: int, budget_type: str, amount: float
    ) -> dict:
        pass

    @abstractmethod
    def update(
        self,
        budget_id: int,
        amount: Optional[float] = None,
        enabled: Optional[bool] = None,
        budget_type: Optional[str] = None,
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def delete(self, budget_id: int) -> bool:
        pass
