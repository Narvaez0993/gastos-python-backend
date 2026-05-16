"""Endpoint del asistente conversacional financiero."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.dependencies.containers import get_ai_chat_service
from app.dependencies.security import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_chat_service import AIChatService
from app.services.expense_service import resolve_tz

router = APIRouter(prefix="/api/chat", tags=["Chat IA"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Enviar un turno al asistente financiero",
)
def chat(
    body: ChatRequest,
    tz: Optional[str] = Query(None),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
    current_user: dict = Depends(get_current_user),
    service: AIChatService = Depends(get_ai_chat_service),
):
    """Procesa el historial completo y devuelve la respuesta del asistente.

    Claude puede llamar tools (get_summary, query_expenses, etc.) en el
    proceso. El cliente NO necesita reenviar las tool_use/tool_result
    intermedias — solo el array conversacional plano."""
    resolved_tz = resolve_tz(tz, x_timezone)
    message, iterations = service.chat(body.messages, current_user["id"], resolved_tz)
    return ChatResponse(
        message=message,
        model=service.settings.CLAUDE_MODEL,
        iterations=iterations,
    )
