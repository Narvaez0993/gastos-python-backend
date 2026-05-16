
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from app.config.settings import Settings
from app.repositories.sql.attachment_sql_repository import AttachmentSqlRepository
from app.schemas.capture import CaptureResponse
from app.services.ai_capture_service import AICaptureService
from app.services.storage_service import StorageBackend

class AttachmentService:
    def __init__(
        self,
        settings: Settings,
        storage: StorageBackend,
        repo: AttachmentSqlRepository,
        ai: AICaptureService,
    ):
        self.settings = settings
        self.storage = storage
        self.repo = repo
        self.ai = ai

    def create_from_upload(self, user_id: int, upload: UploadFile) -> dict:
        mime = (upload.content_type or "").lower()
        allowed = self.settings.allowed_attachment_mimes_list
        if mime not in allowed:
            raise HTTPException(
                status_code=415,
                detail=f"Tipo no soportado: {mime}. Permitidos: {', '.join(allowed)}",
            )

        file_obj = upload.file
        contents = file_obj.read()
        size = len(contents)
        max_bytes = self.settings.MAX_ATTACHMENT_MB * 1024 * 1024
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande (máx {self.settings.MAX_ATTACHMENT_MB} MB)",
            )

        import io
        stored_path = self.storage.save("receipt", user_id, mime, io.BytesIO(contents))

        row = self.repo.create(
            user_id=user_id,
            file_path=str(stored_path),
            mime_type=mime,
            original_name=upload.filename,
            size_bytes=size,
        )
        return row

    def get_owned(self, attachment_id: int, user_id: int) -> dict:
        row = self.repo.get_by_id(attachment_id)
        if not row or row["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Adjunto no encontrado")
        return row

    def read_bytes(self, attachment: dict) -> bytes:
        return self.storage.read(Path(attachment["file_path"]))

    def absolute_path(self, attachment: dict) -> Path:
        return self.storage.absolute(Path(attachment["file_path"]))

    def parse_with_vision(
        self, attachment_id: int, user_id: int, tz: str = "America/Bogota"
    ) -> CaptureResponse:
        att = self.get_owned(attachment_id, user_id)
        data = self.read_bytes(att)
        return self.ai.parse_attachment(data, att["mime_type"], user_id, tz)

    def link(self, attachment_id: int, expense_id: int, user_id: int) -> Optional[dict]:
        att = self.get_owned(attachment_id, user_id)
        return self.repo.link_to_expense(att["id"], expense_id)
