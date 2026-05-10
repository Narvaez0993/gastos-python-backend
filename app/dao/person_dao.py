import sqlite3

from app.database import get_connection, close_connection


class PersonDAO:

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM persons ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_id(person_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM persons WHERE id = ?", (person_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def get_by_name(name):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM persons WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)

    @staticmethod
    def create(name):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO persons (name) VALUES (?)", (name,))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT id, name, created_at FROM persons WHERE id = ?", (new_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def update(person_id, name):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE persons SET name = ? WHERE id = ?",
                (name, person_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            cursor.execute("SELECT id, name, created_at FROM persons WHERE id = ?", (person_id,))
            return dict(cursor.fetchone())
        finally:
            close_connection(conn)

    @staticmethod
    def delete(person_id):
        conn = get_connection()
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
