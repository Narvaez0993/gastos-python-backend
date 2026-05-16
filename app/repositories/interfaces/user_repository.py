
from abc import ABC, abstractmethod
from typing import Optional

class IUserRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[dict]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_email_with_credentials(self, email: str) -> Optional[dict]:
        pass

    @abstractmethod
    def create(self, name: str, email: str, password_hash: str) -> dict:
        pass

    @abstractmethod
    def update_name(self, user_id: int, name: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_email(self, user_id: int, email: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        pass
