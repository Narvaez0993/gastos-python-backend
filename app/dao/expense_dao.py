from app.database import get_connection, close_connection


class ExpenseDAO:

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.person_id, e.amount, e.description, e.category,
                       e.date, e.money_source_id, e.created_at,
                       p.name as person_name,
                       ms.id as ms_id, ms.name as ms_name,
                       ms.balance as ms_balance, ms.enabled as ms_enabled
                FROM expenses e
                JOIN persons p ON e.person_id = p.id
                LEFT JOIN money_sources ms ON e.money_source_id = ms.id
                ORDER BY e.date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_id(expense_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.person_id, e.amount, e.description, e.category,
                       e.date, e.money_source_id, e.created_at,
                       p.name as person_name,
                       ms.id as ms_id, ms.name as ms_name,
                       ms.balance as ms_balance, ms.enabled as ms_enabled
                FROM expenses e
                JOIN persons p ON e.person_id = p.id
                LEFT JOIN money_sources ms ON e.money_source_id = ms.id
                WHERE e.id = ?
            """, (expense_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def create(person_id, amount, description, category, date, money_source_id=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (person_id, amount, description, category, date, money_source_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (person_id, amount, description, category, date, money_source_id))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("""
                SELECT e.id, e.person_id, e.amount, e.description, e.category,
                       e.date, e.money_source_id, e.created_at,
                       p.name as person_name,
                       ms.id as ms_id, ms.name as ms_name,
                       ms.balance as ms_balance, ms.enabled as ms_enabled
                FROM expenses e
                JOIN persons p ON e.person_id = p.id
                LEFT JOIN money_sources ms ON e.money_source_id = ms.id
                WHERE e.id = ?
            """, (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def update(expense_id, amount, description, category, date, money_source_id=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses
                SET amount = ?, description = ?, category = ?, date = ?, money_source_id = ?
                WHERE id = ?
            """, (amount, description, category, date, money_source_id, expense_id))
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute("""
                SELECT e.id, e.person_id, e.amount, e.description, e.category,
                       e.date, e.money_source_id, e.created_at,
                       p.name as person_name,
                       ms.id as ms_id, ms.name as ms_name,
                       ms.balance as ms_balance, ms.enabled as ms_enabled
                FROM expenses e
                JOIN persons p ON e.person_id = p.id
                LEFT JOIN money_sources ms ON e.money_source_id = ms.id
                WHERE e.id = ?
            """, (expense_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def delete(expense_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    @staticmethod
    def get_filtered(person_id=None, start_date=None, end_date=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.id, e.person_id, e.amount, e.description, e.category,
                       e.date, e.money_source_id, e.created_at,
                       p.name as person_name,
                       ms.id as ms_id, ms.name as ms_name,
                       ms.balance as ms_balance, ms.enabled as ms_enabled
                FROM expenses e
                JOIN persons p ON e.person_id = p.id
                LEFT JOIN money_sources ms ON e.money_source_id = ms.id
                WHERE 1=1
            """
            params = []

            if person_id is not None:
                query += " AND e.person_id = ?"
                params.append(person_id)
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

    @staticmethod
    def get_summary(person_id=None, start_date=None, end_date=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()

            where_clauses = []
            params = []
            if person_id is not None:
                where_clauses.append("person_id = ?")
                params.append(person_id)
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

            cursor.execute(f"""
                SELECT COALESCE(category, 'Sin categoría') as category,
                       SUM(amount) as total,
                       COUNT(id) as count
                FROM expenses
                {where_sql}
                GROUP BY COALESCE(category, 'Sin categoría')
                ORDER BY SUM(amount) DESC
            """, params)

            by_category = [dict(row) for row in cursor.fetchall()]

            return {"total": float(total), "by_category": by_category}
        finally:
            close_connection(conn)

    @staticmethod
    def get_spent_in_period(person_id, start_date, end_date):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM expenses
                WHERE person_id = ? AND date >= ? AND date <= ?
            """, (person_id, start_date, end_date))
            return float(cursor.fetchone()["total"])
        finally:
            close_connection(conn)
