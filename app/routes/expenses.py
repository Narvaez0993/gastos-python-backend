from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.dependencies.containers import get_expense_service
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expense_service import ExpenseService, resolve_tz

router = APIRouter(prefix="/api/expenses", tags=["Gastos"])


@router.get("/summary", summary="Resumen de gastos por categoría")
def get_summary(
    personId: Optional[int] = Query(None),
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    service: ExpenseService = Depends(get_expense_service),
):
    """Retorna el total gastado y desglose por categoría."""
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.get_summary(personId, period, startDate, endDate, resolved_tz)


@router.get("/{expense_id}", summary="Obtener gasto por ID")
def get_expense(
    expense_id: int,
    service: ExpenseService = Depends(get_expense_service),
):
    """Retorna un gasto específico por su ID."""
    return service.get_expense(expense_id)


@router.get("", summary="Listar gastos")
def list_expenses(
    personId: Optional[int] = Query(None),
    period: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    service: ExpenseService = Depends(get_expense_service),
):
    """Lista los gastos con filtros opcionales por persona, periodo y fechas."""
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.list_expenses(personId, period, startDate, endDate, resolved_tz)


@router.post("", status_code=201, summary="Crear gasto")
def create_expense(
    data: ExpenseCreate,
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    service: ExpenseService = Depends(get_expense_service),
):
    """Crea un nuevo gasto. Puede vincular una fuente de dinero y verifica presupuestos."""
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.create_expense(data, resolved_tz)


@router.put("/{expense_id}", summary="Actualizar gasto")
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    service: ExpenseService = Depends(get_expense_service),
):
    """Actualiza un gasto existente (monto, descripción, categoría, fecha)."""
    return service.update_expense(expense_id, data)


@router.delete("/{expense_id}", summary="Eliminar gasto")
def delete_expense(
    expense_id: int,
    service: ExpenseService = Depends(get_expense_service),
):
    """Elimina un gasto. Si estaba vinculado a una fuente de dinero, revierte el balance."""
    return service.delete_expense(expense_id)
