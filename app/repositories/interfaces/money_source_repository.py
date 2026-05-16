
from abc import ABC, abstractmethod
from typing import Optional

class IMoneySourceRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[dict]:
        pass

    @abstractmethod
    def get_by_id(self, source_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: int) -> list[dict]:
        pass

    @abstractmethod
    def get_by_user_and_normalized_name(
        self, user_id: int, name_normalized: str
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def create(
        self,
        user_id: int,
        name: str,
        name_normalized: str,
        balance: float = 0,
    ) -> dict:
        pass

    @abstractmethod
    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        name_normalized: Optional[str] = None,
        balance: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def update_balance(self, source_id: int, new_balance: float) -> bool:
        pass

    @abstractmethod
    def delete(self, source_id: int) -> bool:
        pass

    @abstractmethod
    def check_duplicate_name(
        self,
        user_id: int,
        name_normalized: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        pass
