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
    def get_by_user(self, user_id: int) -> list[dict]:
        """Lista los presupuestos del usuario."""

    @abstractmethod
    def get_by_user_and_type(
        self, user_id: int, budget_type: str
    ) -> Optional[dict]:
        """Devuelve el presupuesto por (usuario, tipo). None si no existe."""

    @abstractmethod
    def get_enabled_by_user(self, user_id: int) -> list[dict]:
        """Lista los presupuestos habilitados del usuario (para validación de límites)."""

    @abstractmethod
    def create(
        self, user_id: int, budget_type: str, amount: float
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
