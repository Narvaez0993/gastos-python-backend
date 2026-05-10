"""Contrato para repositorios de Person."""

from abc import ABC, abstractmethod
from typing import Optional


class IPersonRepository(ABC):
    """Interfaz del repositorio de personas. Implementaciones: SQL crudo y JPA (SQLAlchemy)."""

    @abstractmethod
    def get_all(self) -> list[dict]:
        """Devuelve todas las personas ordenadas por nombre ascendente."""

    @abstractmethod
    def get_by_id(self, person_id: int) -> Optional[dict]:
        """Devuelve la persona con el id dado, o None si no existe."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[dict]:
        """Devuelve la persona con el nombre dado, o None si no existe."""

    @abstractmethod
    def create(self, name: str) -> dict:
        """Crea una persona con el nombre dado y devuelve el registro creado."""

    @abstractmethod
    def update(self, person_id: int, name: str) -> Optional[dict]:
        """Actualiza el nombre de la persona. Devuelve el registro actualizado o None si no existía."""

    @abstractmethod
    def delete(self, person_id: int) -> bool:
        """Elimina la persona. Devuelve True si se eliminó, False si no existe o tiene dependencias."""
