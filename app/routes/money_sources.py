from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.money_source import DepositRequest, MoneySourceCreate, MoneySourceUpdate
from app.services.money_source_service import MoneySourceService

router = APIRouter(prefix="/api/money-sources", tags=["Fuentes de Dinero"])


@router.get("", summary="Listar fuentes de dinero")
def list_money_sources(personId: int = Query(...)):
    """Lista las fuentes de dinero de una persona, ordenadas por habilitadas y luego por nombre."""
    return MoneySourceService.list_money_sources(personId)


@router.get("/{source_id}", summary="Obtener fuente de dinero por ID")
def get_money_source(source_id: int):
    """Retorna una fuente de dinero específica por su ID."""
    return MoneySourceService.get_money_source(source_id)


@router.post("", status_code=201, summary="Crear fuente de dinero")
def create_money_source(data: MoneySourceCreate):
    """Crea una nueva fuente de dinero con balance inicial opcional."""
    return MoneySourceService.create_money_source(data)


@router.put("/{source_id}", summary="Actualizar fuente de dinero")
def update_money_source(source_id: int, data: MoneySourceUpdate):
    """Actualiza balance, nombre o estado de una fuente de dinero."""
    return MoneySourceService.update_money_source(source_id, data)


@router.delete("/{source_id}", summary="Eliminar fuente de dinero")
def delete_money_source(source_id: int):
    """Elimina una fuente de dinero (solo si no tiene movimientos)."""
    return MoneySourceService.delete_money_source(source_id)


@router.post("/{source_id}/deposit", status_code=201, summary="Registrar depósito")
def deposit(source_id: int, data: DepositRequest):
    """Registra un depósito o ingreso en una fuente de dinero."""
    return MoneySourceService.deposit(source_id, data)


@router.get("/{source_id}/movements", summary="Historial de movimientos")
def get_movements(
    source_id: int,
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
):
    """Retorna el historial de movimientos de una fuente de dinero con paginación."""
    return MoneySourceService.get_movements(
        source_id, type, startDate, endDate, page, limit
    )
