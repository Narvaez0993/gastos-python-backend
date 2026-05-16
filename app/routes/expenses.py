from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.dependencies.containers import get_expense_service
from app.dependencies.security import get_current_user
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expense_service import ExpenseService, resolve_tz

router = APIRouter(prefix="/api/expenses", tags=["Gastos"])

@router.get("/summary", summary="Resumen de gastos por categoría")
def get_summary(
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.get_summary(current_user["id"], period, startDate, endDate, resolved_tz)

@router.get("/{expense_id}", summary="Obtener gasto por ID")
def get_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    return service.get_expense(expense_id, current_user["id"])

@router.get("", summary="Listar gastos")
def list_expenses(
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.list_expenses(
        current_user["id"], period, startDate, endDate, resolved_tz
    )

@router.post("", status_code=201, summary="Crear gasto")
def create_expense(
    data: ExpenseCreate,
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.create_expense(current_user["id"], data, resolved_tz)

@router.put("/{expense_id}", summary="Actualizar gasto")
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    return service.update_expense(expense_id, current_user["id"], data)

@router.delete("/{expense_id}", summary="Eliminar gasto")
def delete_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    return service.delete_expense(expense_id, current_user["id"])
