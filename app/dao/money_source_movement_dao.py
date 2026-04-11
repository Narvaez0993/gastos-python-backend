import math

from app.database import get_connection, close_connection


class MoneySourceMovementDAO:

    @staticmethod
    def get_by_source(source_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, e.description as expense_description,
                       e.amount as expense_amount, e.category as expense_category
                FROM money_source_movements m
                LEFT JOIN expenses e ON m.expense_id = e.id
                WHERE m.money_source_id = ?
                ORDER BY m.date DESC, m.created_at DESC
            """, (source_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def create(money_source_id, movement_type, amount, balance_before, balance_after,
               date, expense_id=None, note=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO money_source_movements
                    (money_source_id, type, amount, balance_before, balance_after,
                     expense_id, note, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (money_source_id, movement_type, amount, balance_before,
                  balance_after, expense_id, note, date))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("""
                SELECT m.*, e.description as expense_description,
                       e.amount as expense_amount, e.category as expense_category
                FROM money_source_movements m
                LEFT JOIN expenses e ON m.expense_id = e.id
                WHERE m.id = ?
            """, (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def has_movements(source_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM money_source_movements WHERE money_source_id = ?",
                (source_id,),
            )
            return cursor.fetchone()["count"] > 0
        finally:
            close_connection(conn)

    @staticmethod
    def get_filtered(source_id, movement_type=None, start_date=None,
                     end_date=None, page=1, limit=20):
        conn = get_connection()
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
                f"SELECT COUNT(*) as count FROM money_source_movements m WHERE {where_sql}",
                params,
            )
            total = cursor.fetchone()["count"]
            pages = math.ceil(total / limit) if total > 0 else 1

            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT m.*, e.description as expense_description,
                       e.amount as expense_amount, e.category as expense_category
                FROM money_source_movements m
                LEFT JOIN expenses e ON m.expense_id = e.id
                WHERE {where_sql}
                ORDER BY m.date DESC, m.created_at DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset])

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
