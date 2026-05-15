"""Implementación SQL crudo del repositorio de fuentes de dinero."""

from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository

_COLUMNS = (
    "id, user_id, name, name_normalized, balance, enabled, created_at"
)


class MoneySourceSqlRepository(IMoneySourceRepository):
    """Repositorio de fuentes de dinero usando SQL crudo con sqlite3."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources "
                f"ORDER BY enabled DESC, name ASC"
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_id(self, source_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources WHERE id = ?",
                (source_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_by_user(self, user_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources "
                f"WHERE user_id = ? ORDER BY enabled DESC, name ASC",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_user_and_normalized_name(
        self, user_id: int, name_normalized: str
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources "
                f"WHERE user_id = ? AND name_normalized = ?",
                (user_id, name_normalized),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def create(
        self,
        user_id: int,
        name: str,
        name_normalized: str,
        balance: float = 0,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO money_sources (user_id, name, name_normalized, balance) "
                "VALUES (?, ?, ?, ?)",
                (user_id, name, name_normalized, balance),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources WHERE id = ?",
                (new_id,),
            )
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        name_normalized: Optional[str] = None,
        balance: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            fields = []
            params = []

            if name is not None:
                fields.append("name = ?")
                params.append(name)
            if name_normalized is not None:
                fields.append("name_normalized = ?")
                params.append(name_normalized)
            if balance is not None:
                fields.append("balance = ?")
                params.append(balance)
            if enabled is not None:
                fields.append("enabled = ?")
                params.append(1 if enabled else 0)

            if not fields:
                return self.get_by_id(source_id)

            params.append(source_id)
            cursor.execute(
                f"UPDATE money_sources SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute(
                f"SELECT {_COLUMNS} FROM money_sources WHERE id = ?",
                (source_id,),
            )
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update_balance(self, source_id: int, new_balance: float) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE money_sources SET balance = ? WHERE id = ?",
                (new_balance, source_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    def delete(self, source_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM money_sources WHERE id = ?", (source_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    def check_duplicate_name(
        self,
        user_id: int,
        name_normalized: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT id FROM money_sources "
                    "WHERE user_id = ? AND name_normalized = ? AND id != ?",
                    (user_id, name_normalized, exclude_id),
                )
            else:
                cursor.execute(
                    "SELECT id FROM money_sources "
                    "WHERE user_id = ? AND name_normalized = ?",
                    (user_id, name_normalized),
                )
            return cursor.fetchone() is not None
        finally:
            close_connection(conn)
