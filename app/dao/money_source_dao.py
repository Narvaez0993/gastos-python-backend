from app.database import get_connection, close_connection


class MoneySourceDAO:

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM money_sources ORDER BY enabled DESC, name ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_id(source_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM money_sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_person(person_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM money_sources WHERE person_id = ? ORDER BY enabled DESC, name ASC",
                (person_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_person_and_normalized_name(person_id, name_normalized):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM money_sources WHERE person_id = ? AND name_normalized = ?",
                (person_id, name_normalized),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def create(person_id, name, name_normalized, balance=0):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO money_sources (person_id, name, name_normalized, balance)
                VALUES (?, ?, ?, ?)
            """, (person_id, name, name_normalized, balance))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM money_sources WHERE id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def update(source_id, name=None, name_normalized=None, balance=None, enabled=None):
        conn = get_connection()
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
                return MoneySourceDAO.get_by_id(source_id)

            params.append(source_id)
            cursor.execute(
                f"UPDATE money_sources SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute("SELECT * FROM money_sources WHERE id = ?", (source_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def update_balance(source_id, new_balance):
        conn = get_connection()
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

    @staticmethod
    def delete(source_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM money_sources WHERE id = ?", (source_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            close_connection(conn)

    @staticmethod
    def check_duplicate_name(person_id, name_normalized, exclude_id=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT id FROM money_sources WHERE person_id = ? AND name_normalized = ? AND id != ?",
                    (person_id, name_normalized, exclude_id),
                )
            else:
                cursor.execute(
                    "SELECT id FROM money_sources WHERE person_id = ? AND name_normalized = ?",
                    (person_id, name_normalized),
                )
            return cursor.fetchone() is not None
        finally:
            close_connection(conn)
