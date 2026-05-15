"""Schemas Pydantic para adjuntos (recibos, facturas)."""

from typing import Optional

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: int
    user_id: int
    expense_id: Optional[int] = None
    mime_type: str
    original_name: Optional[str] = None
    size_bytes: int
    created_at: str


class CaptureReceiptRequest(BaseModel):
    attachment_id: int
