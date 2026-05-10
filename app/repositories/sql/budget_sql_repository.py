"""Implementación SQL crudo del repositorio de presupuestos."""

from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.budget_repository import IBudgetRepository

_BASE_SELECT = """
    SELECT b.id, b.person_id, b.type, b.amount, b.enabled, b.created_at,
           p.name as person_name
    FROM budgets b
    JOIN persons p ON b.person_id = p.id
"""


class BudgetSqlRepository(IBudgetRepository):
    """Repositorio de presupuestos usando SQL crudo con sqlite3."""

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

    def get_by_person(self, person_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " WHERE b.person_id = ?", (person_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_person_and_type(
        self, person_id: int, budget_type: str
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                _BASE_SELECT + " WHERE b.person_id = ? AND b.type = ?",
                (person_id, budget_type),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def get_enabled_by_person(self, person_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, person_id, type, amount, enabled, created_at "
                "FROM budgets WHERE person_id = ? AND enabled = 1",
                (person_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def create(self, person_id: int, budget_type: str, amount: float) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO budgets (person_id, type, amount) VALUES (?, ?, ?)",
                (person_id, budget_type, amount),
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
