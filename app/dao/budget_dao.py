from app.database import get_connection, close_connection


class BudgetDAO:

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                ORDER BY b.id
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_id(budget_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                WHERE b.id = ?
            """, (budget_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_person(person_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                WHERE b.person_id = ?
            """, (person_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_person_and_type(person_id, budget_type):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                WHERE b.person_id = ? AND b.type = ?
            """, (person_id, budget_type))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def get_enabled_by_person(person_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM budgets WHERE person_id = ? AND enabled = 1",
                (person_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def create(person_id, budget_type, amount):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (person_id, type, amount)
                VALUES (?, ?, ?)
            """, (person_id, budget_type, amount))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                WHERE b.id = ?
            """, (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def update(budget_id, amount=None, enabled=None, budget_type=None):
        conn = get_connection()
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
                return BudgetDAO.get_by_id(budget_id)

            params.append(budget_id)
            cursor.execute(
                f"UPDATE budgets SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute("""
                SELECT b.*, p.name as person_name
                FROM budgets b
                JOIN persons p ON b.person_id = p.id
                WHERE b.id = ?
            """, (budget_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def delete(budget_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)
