
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse

from app.dependencies.containers import get_attachment_service
from app.dependencies.security import get_current_user
from app.schemas.attachment import AttachmentOut
from app.services.attachment_service import AttachmentService

router = APIRouter(prefix="/api/attachments", tags=["Adjuntos"])

@router.post(
    "",
    response_model=AttachmentOut,
    status_code=201,
    summary="Subir un adjunto (recibo/factura)",
)
def upload_attachment(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    service: AttachmentService = Depends(get_attachment_service),
):
    return service.create_from_upload(current_user["id"], file)

@router.get(
    "/{attachment_id}",
    summary="Descargar el archivo de un adjunto",
)
def download_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
    service: AttachmentService = Depends(get_attachment_service),
):
    att = service.get_owned(attachment_id, current_user["id"])

    def iterfile():
        path = service.absolute_path(att)
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(64 * 1024)
                if not chunk:
                    break
                yield chunk

    headers = {
        "Content-Disposition": f'inline; filename="{att.get("original_name") or "attachment"}"',
    }
    return StreamingResponse(iterfile(), media_type=att["mime_type"], headers=headers)
