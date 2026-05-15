"""Servicio de almacenamiento de archivos. Interface-driven para permitir swap
a S3/MinIO en el futuro sin tocar los services."""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from app.config.settings import Settings


MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "application/pdf": ".pdf",
}


class StorageBackend(ABC):
    @abstractmethod
    def save(self, scope: str, user_id: int, mime_type: str, file: BinaryIO) -> Path:
        ...

    @abstractmethod
    def read(self, path: Path) -> bytes:
        ...

    @abstractmethod
    def absolute(self, path: Path) -> Path:
        ...


class LocalFilesystemBackend(StorageBackend):
    """Implementación filesystem. Estructura: {root}/{scope}/{user_id}/{YYYY-MM-DD}/{uuid}.{ext}"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = Path(settings.get_uploads_absolute_path())
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, scope: str, user_id: int, mime_type: str, file: BinaryIO) -> Path:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ext = MIME_TO_EXT.get(mime_type, ".bin")
        rel_dir = Path(scope) / str(user_id) / today
        abs_dir = self.root / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)
        # 0700 para directorios
        try:
            os.chmod(abs_dir, 0o700)
        except OSError:
            pass
        filename = f"{uuid.uuid4().hex}{ext}"
        abs_path = abs_dir / filename
        with open(abs_path, "wb") as out:
            while True:
                chunk = file.read(64 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        try:
            os.chmod(abs_path, 0o600)
        except OSError:
            pass
        return rel_dir / filename

    def read(self, path: Path) -> bytes:
        return (self.root / path).read_bytes()

    def absolute(self, path: Path) -> Path:
        return self.root / path
