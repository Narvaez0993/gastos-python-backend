"""Schemas Pydantic para el flujo de captura de gastos con IA."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CaptureTextRequest(BaseModel):
    """Texto en lenguaje natural a parsear por Claude."""

    text: str = Field(min_length=1, max_length=2000)


class ParsedExpenseItem(BaseModel):
    """Un gasto detectado por Claude a partir del texto/audio."""

    amount: int = Field(ge=0, description="Monto en COP, entero (sin decimales).")
    description: str = Field(min_length=1, max_length=140)
    category: Optional[str] = Field(
        default=None,
        description="Categoría de la lista provista o null si no aplica.",
    )
    money_source_id: Optional[int] = Field(
        default=None,
        description="ID de la fuente de dinero si Claude la mapea con confianza.",
    )
    confidence: Literal["alta", "media", "baja"] = "media"
    notes: Optional[str] = Field(
        default=None,
        description="Razonamiento corto/aclaración del modelo (opcional).",
    )


class CaptureResponse(BaseModel):
    """Respuesta unificada de los endpoints /capture/*."""

    items: List[ParsedExpenseItem]
    transcript: str
    model: str
