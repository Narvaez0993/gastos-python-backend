"""Contrato para repositorios de User."""

from abc import ABC, abstractmethod
from typing import Optional


class IUserRepository(ABC):
    """Interfaz del repositorio de usuarios. Implementaciones: SQL crudo y JPA (SQLAlchemy).

    Convención: `get_by_id` y `get_by_email` NUNCA devuelven el `password_hash`.
    Solo `get_by_email_with_credentials` lo expone, y debe usarse únicamente desde
    el AuthService al verificar credenciales en login.
    """

    @abstractmethod
    def get_all(self) -> list[dict]:
        """Devuelve todos los usuarios ordenados por nombre ascendente (sin password_hash)."""

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[dict]:
        """Devuelve el usuario con el id dado, o None si no existe (sin password_hash)."""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[dict]:
        """Devuelve el usuario con el email dado, o None si no existe (sin password_hash)."""

    @abstractmethod
    def get_by_email_with_credentials(self, email: str) -> Optional[dict]:
        """Devuelve el usuario incluyendo `password_hash`. Solo para verificación de login."""

    @abstractmethod
    def create(self, name: str, email: str, password_hash: str) -> dict:
        """Crea un usuario y devuelve el registro creado (sin password_hash)."""

    @abstractmethod
    def update_name(self, user_id: int, name: str) -> Optional[dict]:
        """Actualiza el display name. Devuelve el registro o None si no existía."""

    @abstractmethod
    def update_email(self, user_id: int, email: str) -> Optional[dict]:
        """Actualiza el email. Devuelve el registro o None si no existía."""

    @abstractmethod
    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        """Actualiza el password_hash. Devuelve True si se actualizó, False si no existe."""

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Elimina el usuario. Devuelve True si se eliminó, False si no existe o tiene dependencias."""
