"""Schemas Pydantic para el chat conversacional con la IA financiera."""

from typing import Any, List, Literal, Union

from pydantic import BaseModel, Field


# `content` puede ser un string simple (mensaje plano) o una lista de bloques
# (cuando Claude devolvió tool_use o cuando enviamos tool_result en la siguiente
# vuelta). Mantenemos la lista como `list[Any]` porque su shape lo define la API
# de Anthropic (text, tool_use, tool_result blocks) y validarlo en Pydantic
# duplicaría el contrato. La validación de seguridad sigue siendo el `role`.
ChatRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    """Un mensaje de la conversación. Mantiene compatibilidad con el formato
    que espera/devuelve `client.messages.create` de Anthropic."""

    role: ChatRole
    content: Union[str, List[Any]]


class ChatRequest(BaseModel):
    """Historial completo de la conversación. El backend NO persiste — el
    cliente envía todo el array en cada turno."""

    messages: List[ChatMessage] = Field(min_length=1, max_length=40)


class ChatResponse(BaseModel):
    """Respuesta del asistente para el turno actual."""

    message: ChatMessage
    model: str
    iterations: int = Field(
        description="Número de vueltas que dio el loop de tool_use antes de "
        "producir la respuesta final.",
    )
