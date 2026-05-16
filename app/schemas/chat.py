
from typing import Any, List, Literal, Union

from pydantic import BaseModel, Field

ChatRole = Literal["user", "assistant"]

class ChatMessage(BaseModel):

    role: ChatRole
    content: Union[str, List[Any]]

class ChatRequest(BaseModel):

    messages: List[ChatMessage] = Field(min_length=1, max_length=40)

class ChatResponse(BaseModel):

    message: ChatMessage
    model: str
    iterations: int = Field(
        description="Número de vueltas que dio el loop de tool_use antes de "
        "producir la respuesta final.",
    )
