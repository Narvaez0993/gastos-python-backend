"""Implementación SQL crudo del repositorio de movimientos de fuentes de dinero."""

import math
from typing import Optional

from app.database import close_connection, get_connection
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)

_BASE_SELECT = """
    SELECT m.id, m.money_source_id, m.type, m.amount,
           m.balance_before, m.balance_after, m.expense_id,
           m.note, m.date, m.created_at,
           e.description as expense_description,
           e.amount as expense_amount, e.category as expense_category
    FROM money_source_movements m
    LEFT JOIN expenses e ON m.expense_id = e.id
"""


class MoneySourceMovementSqlRepository(IMoneySourceMovementRepository):
    """Repositorio de movimientos usando SQL crudo con sqlite3."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    def get_by_source(self, source_id: int) -> list[dict]:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                _BASE_SELECT
                + " WHERE m.money_source_id = ? "
                + "ORDER BY m.date DESC, m.created_at DESC",
                (source_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    def create(
        self,
        money_source_id: int,
        movement_type: str,
        amount: float,
        balance_before: float,
        balance_after: float,
        date: str,
        expense_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO money_source_movements "
                "(money_source_id, type, amount, balance_before, balance_after, "
                "expense_id, note, date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    money_source_id, movement_type, amount, balance_before,
                    balance_after, expense_id, note, date,
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(_BASE_SELECT + " WHERE m.id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    def has_movements(self, source_id: int) -> bool:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM money_source_movements "
                "WHERE money_source_id = ?",
                (source_id,),
            )
            return cursor.fetchone()["count"] > 0
        finally:
            close_connection(conn)

    def get_filtered(
        self,
        source_id: int,
        movement_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        conn = self._conn()
        try:
            cursor = conn.cursor()
            page = max(1, page)
            limit = max(1, min(100, limit))

            where_clauses = ["m.money_source_id = ?"]
            params = [source_id]

            if movement_type:
                where_clauses.append("m.type = ?")
                params.append(movement_type)
            if start_date:
                where_clauses.append("m.date >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("m.date <= ?")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses)

            cursor.execute(
                f"SELECT COUNT(*) as count FROM money_source_movements m "
                f"WHERE {where_sql}",
                params,
            )
            total = cursor.fetchone()["count"]
            pages = math.ceil(total / limit) if total > 0 else 1

            offset = (page - 1) * limit
            cursor.execute(
                _BASE_SELECT
                + f" WHERE {where_sql} "
                + "ORDER BY m.date DESC, m.created_at DESC "
                + "LIMIT ? OFFSET ?",
                params + [limit, offset],
            )

            movements = [dict(row) for row in cursor.fetchall()]

            return {
                "movements": movements,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": pages,
                },
            }
        finally:
            close_connection(conn)
