"""Contrato para repositorios de MoneySource (fuentes de dinero)."""

from abc import ABC, abstractmethod
from typing import Optional


class IMoneySourceRepository(ABC):
    """Interfaz del repositorio de fuentes de dinero. Implementaciones: SQL crudo y JPA."""

    @abstractmethod
    def get_all(self) -> list[dict]:
        """Devuelve todas las fuentes ordenadas: habilitadas primero, luego por nombre."""

    @abstractmethod
    def get_by_id(self, source_id: int) -> Optional[dict]:
        """Devuelve la fuente con el id dado, o None si no existe."""

    @abstractmethod
    def get_by_person(self, person_id: int) -> list[dict]:
        """Devuelve las fuentes de la persona ordenadas: habilitadas primero, luego por nombre."""

    @abstractmethod
    def get_by_person_and_normalized_name(
        self, person_id: int, name_normalized: str
    ) -> Optional[dict]:
        """Busca por dueño y nombre normalizado (clave de unicidad). None si no existe."""

    @abstractmethod
    def create(
        self,
        person_id: int,
        name: str,
        name_normalized: str,
        balance: float = 0,
    ) -> dict:
        """Crea una nueva fuente y devuelve el registro creado."""

    @abstractmethod
    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        name_normalized: Optional[str] = None,
        balance: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[dict]:
        """Actualiza los campos no nulos. Devuelve el registro actualizado o None si no existe."""

    @abstractmethod
    def update_balance(self, source_id: int, new_balance: float) -> bool:
        """Actualiza solo el balance. Útil tras un gasto o depósito."""

    @abstractmethod
    def delete(self, source_id: int) -> bool:
        """Elimina la fuente. Devuelve True si se eliminó."""

    @abstractmethod
    def check_duplicate_name(
        self,
        person_id: int,
        name_normalized: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Verifica si ya existe otra fuente del mismo dueño con el mismo nombre normalizado."""
