from fastapi import APIRouter, Query

from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/budgets", tags=["Presupuestos"])


@router.get("", summary="Listar presupuestos por persona")
def list_budgets(personName: str = Query(...)):
    """Retorna todos los presupuestos de una persona."""
    return BudgetService.list_budgets(personName)


@router.get("/{budget_id}", summary="Obtener presupuesto por ID")
def get_budget(budget_id: int):
    """Retorna un presupuesto específico por su ID."""
    return BudgetService.get_budget(budget_id)


@router.post("", status_code=201, summary="Crear o actualizar presupuesto")
def create_or_update_budget(data: BudgetCreate):
    """Crea un presupuesto o actualiza el existente si ya hay uno del mismo tipo para la persona."""
    return BudgetService.create_or_update_budget(data)


@router.put("/{budget_id}", summary="Actualizar presupuesto")
def update_budget(budget_id: int, data: BudgetUpdate):
    """Actualiza un presupuesto existente (monto, tipo, habilitado)."""
    return BudgetService.update_budget(budget_id, data)


@router.delete("/{budget_id}", summary="Eliminar presupuesto")
def delete_budget(budget_id: int):
    """Elimina un presupuesto del sistema."""
    return BudgetService.delete_budget(budget_id)
