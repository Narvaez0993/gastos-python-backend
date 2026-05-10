from fastapi import APIRouter, Depends, Query

from app.dependencies.containers import get_budget_service
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/budgets", tags=["Presupuestos"])


@router.get("", summary="Listar presupuestos por persona")
def list_budgets(
    personId: int = Query(...),
    service: BudgetService = Depends(get_budget_service),
):
    """Retorna todos los presupuestos de una persona."""
    return service.list_budgets(personId)


@router.get("/{budget_id}", summary="Obtener presupuesto por ID")
def get_budget(
    budget_id: int,
    service: BudgetService = Depends(get_budget_service),
):
    """Retorna un presupuesto específico por su ID."""
    return service.get_budget(budget_id)


@router.post("", status_code=201, summary="Crear o actualizar presupuesto")
def create_or_update_budget(
    data: BudgetCreate,
    service: BudgetService = Depends(get_budget_service),
):
    """Crea un presupuesto o actualiza el existente si ya hay uno del mismo tipo para la persona."""
    return service.create_or_update_budget(data)


@router.put("/{budget_id}", summary="Actualizar presupuesto")
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    service: BudgetService = Depends(get_budget_service),
):
    """Actualiza un presupuesto existente (monto, tipo, habilitado)."""
    return service.update_budget(budget_id, data)


@router.delete("/{budget_id}", summary="Eliminar presupuesto")
def delete_budget(
    budget_id: int,
    service: BudgetService = Depends(get_budget_service),
):
    """Elimina un presupuesto del sistema."""
    return service.delete_budget(budget_id)
