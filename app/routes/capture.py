
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.dependencies.containers import (
    get_ai_capture_service,
    get_attachment_service,
)
from app.dependencies.security import get_current_user
from app.schemas.attachment import CaptureReceiptRequest
from app.schemas.capture import CaptureResponse, CaptureTextRequest
from app.services.ai_capture_service import AICaptureService
from app.services.attachment_service import AttachmentService
from app.services.expense_service import resolve_tz

router = APIRouter(prefix="/api/capture", tags=["Captura IA"])

@router.post(
    "/text",
    response_model=CaptureResponse,
    summary="Parsear texto en lenguaje natural a gastos estructurados",
)
def capture_text(
    body: CaptureTextRequest,
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: AICaptureService = Depends(get_ai_capture_service),
):
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.parse_text(body.text, current_user["id"], resolved_tz)

@router.post(
    "/receipt",
    response_model=CaptureResponse,
    summary="Parsear un recibo/factura adjunto con Claude Vision",
)
def capture_receipt(
    body: CaptureReceiptRequest,
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: AttachmentService = Depends(get_attachment_service),
):
    resolved_tz = resolve_tz(tz, x_timezone)
    return service.parse_with_vision(
        body.attachment_id, current_user["id"], resolved_tz
    )
