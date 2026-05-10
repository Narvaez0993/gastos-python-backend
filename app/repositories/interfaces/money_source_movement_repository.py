"""Contrato para repositorios de MoneySourceMovement (movimientos de fuentes)."""

from abc import ABC, abstractmethod
from typing import Optional


class IMoneySourceMovementRepository(ABC):
    """Interfaz del repositorio de movimientos. Implementación actual: SQL crudo."""

    @abstractmethod
    def get_by_source(self, source_id: int) -> list[dict]:
        """Devuelve todos los movimientos de la fuente, más recientes primero."""

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
        """Crea un movimiento y devuelve el registro creado."""

    @abstractmethod
    def has_movements(self, source_id: int) -> bool:
        """Indica si la fuente tiene al menos un movimiento (bloquea borrados)."""

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
        """Lista paginada de movimientos. Estructura: {'movements': [...], 'pagination': {...}}."""
