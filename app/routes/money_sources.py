from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies.containers import get_money_source_service
from app.schemas.money_source import DepositRequest, MoneySourceCreate, MoneySourceUpdate
from app.services.money_source_service import MoneySourceService

router = APIRouter(prefix="/api/money-sources", tags=["Fuentes de Dinero"])


@router.get("", summary="Listar fuentes de dinero")
def list_money_sources(
    personId: int = Query(...),
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Lista las fuentes de dinero de una persona, ordenadas por habilitadas y luego por nombre."""
    return service.list_money_sources(personId)


@router.get("/{source_id}", summary="Obtener fuente de dinero por ID")
def get_money_source(
    source_id: int,
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Retorna una fuente de dinero específica por su ID."""
    return service.get_money_source(source_id)


@router.post("", status_code=201, summary="Crear fuente de dinero")
def create_money_source(
    data: MoneySourceCreate,
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Crea una nueva fuente de dinero con balance inicial opcional."""
    return service.create_money_source(data)


@router.put("/{source_id}", summary="Actualizar fuente de dinero")
def update_money_source(
    source_id: int,
    data: MoneySourceUpdate,
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Actualiza balance, nombre o estado de una fuente de dinero."""
    return service.update_money_source(source_id, data)


@router.delete("/{source_id}", summary="Eliminar fuente de dinero")
def delete_money_source(
    source_id: int,
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Elimina una fuente de dinero (solo si no tiene movimientos)."""
    return service.delete_money_source(source_id)


@router.post("/{source_id}/deposit", status_code=201, summary="Registrar depósito")
def deposit(
    source_id: int,
    data: DepositRequest,
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Registra un depósito o ingreso en una fuente de dinero."""
    return service.deposit(source_id, data)


@router.get("/{source_id}/movements", summary="Historial de movimientos")
def get_movements(
    source_id: int,
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
    service: MoneySourceService = Depends(get_money_source_service),
):
    """Retorna el historial de movimientos de una fuente de dinero con paginación."""
    return service.get_movements(source_id, type, startDate, endDate, page, limit)
