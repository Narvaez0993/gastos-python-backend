"""Contrato para repositorios de Budget (presupuestos)."""

from abc import ABC, abstractmethod
from typing import Optional


class IBudgetRepository(ABC):
    """Interfaz del repositorio de presupuestos. Implementación actual: SQL crudo."""

    @abstractmethod
    def get_all(self) -> list[dict]:
        """Devuelve todos los presupuestos con el nombre del dueño."""

    @abstractmethod
    def get_by_id(self, budget_id: int) -> Optional[dict]:
        """Devuelve el presupuesto por id, o None si no existe."""

    @abstractmethod
    def get_by_person(self, person_id: int) -> list[dict]:
        """Lista los presupuestos de la persona."""

    @abstractmethod
    def get_by_person_and_type(
        self, person_id: int, budget_type: str
    ) -> Optional[dict]:
        """Devuelve el presupuesto por (persona, tipo). None si no existe."""

    @abstractmethod
    def get_enabled_by_person(self, person_id: int) -> list[dict]:
        """Lista los presupuestos habilitados de la persona (para validación de límites)."""

    @abstractmethod
    def create(
        self, person_id: int, budget_type: str, amount: float
    ) -> dict:
        """Crea un presupuesto y devuelve el registro creado."""

    @abstractmethod
    def update(
        self,
        budget_id: int,
        amount: Optional[float] = None,
        enabled: Optional[bool] = None,
        budget_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Actualiza los campos no nulos. Devuelve el registro actualizado."""

    @abstractmethod
    def delete(self, budget_id: int) -> bool:
        """Elimina el presupuesto. Devuelve True si se eliminó."""
