"""Contrato para repositorios de Expense (gastos)."""

from abc import ABC, abstractmethod
from typing import Optional


class IExpenseRepository(ABC):
    """Interfaz del repositorio de gastos. Implementación actual: SQL crudo."""

    @abstractmethod
    def get_all(self) -> list[dict]:
        """Devuelve todos los gastos con datos de persona y fuente, ordenados por fecha desc."""

    @abstractmethod
    def get_by_id(self, expense_id: int) -> Optional[dict]:
        """Devuelve el gasto con sus joins, o None si no existe."""

    @abstractmethod
    def create(
        self,
        person_id: int,
        amount: float,
        description: str,
        category: Optional[str],
        date: str,
        money_source_id: Optional[int] = None,
    ) -> dict:
        """Crea un gasto y devuelve el registro creado con joins."""

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
        """Actualiza el gasto. Devuelve el registro actualizado o None si no existe."""

    @abstractmethod
    def delete(self, expense_id: int) -> bool:
        """Elimina el gasto. Devuelve True si se eliminó."""

    @abstractmethod
    def get_filtered(
        self,
        person_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        """Lista gastos filtrados por persona y rango de fechas (inclusive)."""

    @abstractmethod
    def get_summary(
        self,
        person_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Devuelve total y suma agrupada por categoría. {'total': float, 'by_category': [...]}"""

    @abstractmethod
    def get_spent_in_period(
        self, person_id: int, start_date: str, end_date: str
    ) -> float:
        """Suma de gastos de la persona en el rango. 0 si no hay."""
