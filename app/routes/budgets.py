from fastapi import APIRouter, Depends

from app.dependencies.containers import get_budget_service
from app.dependencies.security import get_current_user
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/budgets", tags=["Presupuestos"])

@router.get("", summary="Listar presupuestos del usuario actual")
def list_budgets(
    current_user: dict = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.list_budgets(current_user["id"])

@router.get("/{budget_id}", summary="Obtener presupuesto por ID")
def get_budget(
    budget_id: int,
    current_user: dict = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.get_budget(budget_id, current_user["id"])

@router.post("", status_code=201, summary="Crear o actualizar presupuesto")
def create_or_update_budget(
    data: BudgetCreate,
    current_user: dict = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.create_or_update_budget(current_user["id"], data)

@router.put("/{budget_id}", summary="Actualizar presupuesto")
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user: dict = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.update_budget(budget_id, current_user["id"], data)

@router.delete("/{budget_id}", summary="Eliminar presupuesto")
def delete_budget(
    budget_id: int,
    current_user: dict = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.delete_budget(budget_id, current_user["id"])
