
from typing import Optional

from app.database import close_connection, get_connection

class AttachmentSqlRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def create(
        self,
        user_id: int,
        file_path: str,
        mime_type: str,
        original_name: Optional[str],
        size_bytes: int,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attachments "
                "(user_id, file_path, mime_type, original_name, size_bytes) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, file_path, mime_type, original_name, size_bytes),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM attachments WHERE id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def get_by_id(self, attachment_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def list_by_expense(self, expense_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM attachments WHERE expense_id = ? ORDER BY id ASC",
                (expense_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def link_to_expense(self, attachment_id: int, expense_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE attachments SET expense_id = ? WHERE id = ?",
                (expense_id, attachment_id),
            )
            conn.commit()
            cursor.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def delete(self, attachment_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)
