
from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.expense_repository import IExpenseRepository

_BASE_SELECT = """
    SELECT e.id, e.user_id, e.amount, e.description, e.category,
           e.date, e.money_source_id, e.created_at,
           u.name as user_name,
           ms.id as ms_id, ms.name as ms_name,
           ms.balance as ms_balance, ms.enabled as ms_enabled
    FROM expenses e
    JOIN users u ON e.user_id = u.id
    LEFT JOIN money_sources ms ON e.money_source_id = ms.id
"""

class ExpenseSqlRepository(IExpenseRepository):

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " ORDER BY e.date DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_by_id(self, expense_id: int) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(_BASE_SELECT + " WHERE e.id = ?", (expense_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    def create(
        self,
        user_id: int,
        amount: float,
        description: str,
        category: Optional[str],
        date: str,
        money_source_id: Optional[int] = None,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses "
                "(user_id, amount, description, category, date, money_source_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, amount, description, category, date, money_source_id),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(_BASE_SELECT + " WHERE e.id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def update(
        self,
        expense_id: int,
        amount: float,
        description: str,
        category: Optional[str],
        date: str,
        money_source_id: Optional[int] = None,
    ) -> Optional[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE expenses "
                "SET amount = ?, description = ?, category = ?, date = ?, "
                "money_source_id = ? WHERE id = ?",
                (amount, description, category, date, money_source_id, expense_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute(_BASE_SELECT + " WHERE e.id = ?", (expense_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def delete(self, expense_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    def get_filtered(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            query = _BASE_SELECT + " WHERE 1=1"
            params = []

            if user_id is not None:
                query += " AND e.user_id = ?"
                params.append(user_id)
            if start_date is not None:
                query += " AND e.date >= ?"
                params.append(start_date)
            if end_date is not None:
                query += " AND e.date <= ?"
                params.append(end_date)

            query += " ORDER BY e.date DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def get_summary(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()

            where_clauses = []
            params = []
            if user_id is not None:
                where_clauses.append("user_id = ?")
                params.append(user_id)
            if start_date is not None:
                where_clauses.append("date >= ?")
                params.append(start_date)
            if end_date is not None:
                where_clauses.append("date <= ?")
                params.append(end_date)

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0) as total FROM expenses {where_sql}",
                params,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT COALESCE(category, 'Sin categoría') as category,
                       SUM(amount) as total,
                       COUNT(id) as count
                FROM expenses
                {where_sql}
                GROUP BY COALESCE(category, 'Sin categoría')
                ORDER BY SUM(amount) DESC
                """,
                params,
            )

            by_category = [dict(row) for row in cursor.fetchall()]

            return {"total": float(total), "by_category": by_category}
        finally:
            close_connection(conn)

    def get_spent_in_period(
        self, user_id: int, start_date: str, end_date: str
    ) -> float:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expenses "
                "WHERE user_id = ? AND date >= ? AND date <= ?",
                (user_id, start_date, end_date),
            )
            return float(cursor.fetchone()["total"])
        finally:
            close_connection(conn)
