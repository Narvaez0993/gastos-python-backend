
from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.budget_repository import IBudgetRepository

_BASE_SELECT = """
    SELECT b.id, b.user_id, b.type, b.amount, b.enabled, b.created_at,
           u.name as user_name
    FROM budgets b
    JOIN users u ON b.user_id = u.id
"""

class BudgetSqlRepository(IBudgetRepository):

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " ORDER BY b.id")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_id(self, budget_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " WHERE b.id = ?", (budget_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_by_user(self, user_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " WHERE b.user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_user_and_type(
        self, user_id: int, budget_type: str
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                _BASE_SELECT + " WHERE b.user_id = ? AND b.type = ?",
                (user_id, budget_type),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_enabled_by_user(self, user_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, user_id, type, amount, enabled, created_at "
                "FROM budgets WHERE user_id = ? AND enabled = 1",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def create(self, user_id: int, budget_type: str, amount: float) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO budgets (user_id, type, amount) VALUES (?, ?, ?)",
                (user_id, budget_type, amount),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(_BASE_SELECT + " WHERE b.id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update(
        self,
        budget_id: int,
        amount: Optional[float] = None,
        enabled: Optional[bool] = None,
        budget_type: Optional[str] = None,
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            fields = []
            params = []

            if amount is not None:
                fields.append("amount = ?")
                params.append(amount)
            if enabled is not None:
                fields.append("enabled = ?")
                params.append(1 if enabled else 0)
            if budget_type is not None:
                fields.append("type = ?")
                params.append(budget_type)

            if not fields:
                return self.get_by_id(budget_id)

            params.append(budget_id)
            cursor.execute(
                f"UPDATE budgets SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute(_BASE_SELECT + " WHERE b.id = ?", (budget_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def delete(self, budget_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)
