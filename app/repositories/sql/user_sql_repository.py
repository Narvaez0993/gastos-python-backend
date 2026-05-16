
import sqlite3
from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.user_repository import IUserRepository

_PUBLIC_COLUMNS = "id, name, email, created_at"

class UserSqlRepository(IUserRepository):

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {_PUBLIC_COLUMNS} FROM users ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_id(self, user_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_by_email(self, email: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE email = ?",
                (email,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_by_email_with_credentials(self, email: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
                (email,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def create(self, name: str, email: str, password_hash: str) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = ?",
                (new_id,),
            )
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update_name(self, user_id: int, name: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (name, user_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            return self.get_by_id(user_id)
        finally:
            close_connection(conn)

    def update_email(self, user_id: int, email: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (email, user_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            return self.get_by_id(user_id)
        finally:
            close_connection(conn)

    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    def delete(self, user_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        finally:
            close_connection(conn)
