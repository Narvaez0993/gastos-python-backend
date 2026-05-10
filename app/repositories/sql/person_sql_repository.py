"""Implementación SQL crudo del repositorio de personas."""

import sqlite3
from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.person_repository import IPersonRepository


class PersonSqlRepository(IPersonRepository):
    """Repositorio de personas usando SQL crudo con sqlite3."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM persons ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_id(self, person_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, created_at FROM persons WHERE id = ?",
                (person_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_by_name(self, name: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, created_at FROM persons WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def create(self, name: str) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO persons (name) VALUES (?)", (name,))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, name, created_at FROM persons WHERE id = ?",
                (new_id,),
            )
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update(self, person_id: int, name: str) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE persons SET name = ? WHERE id = ?",
                (name, person_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute(
                "SELECT id, name, created_at FROM persons WHERE id = ?",
                (person_id,),
            )
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def delete(self, person_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM persons WHERE id = ?", (person_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        finally:
            close_connection(conn)
