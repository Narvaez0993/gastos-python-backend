import sqlite3

from app.config.settings import get_settings


def get_connection():
    """Abre una nueva conexión a la base de datos SQLite de manera manual."""
    conn = sqlite3.connect(get_settings().get_database_absolute_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_connection(conn):
    """Cierra una conexión a la base de datos de manera manual."""
    if conn:
        conn.close()


def init_db():
    """Crea todas las tablas si no existen, usando SQL crudo."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                date TEXT NOT NULL,
                money_source_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (person_id) REFERENCES persons(id),
                FOREIGN KEY (money_source_id) REFERENCES money_sources(id)
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('daily', 'weekly', 'monthly')),
                amount REAL NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(person_id, type),
                FOREIGN KEY (person_id) REFERENCES persons(id)
            );

            CREATE TABLE IF NOT EXISTS money_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                name_normalized TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(person_id, name_normalized),
                FOREIGN KEY (person_id) REFERENCES persons(id)
            );

            CREATE TABLE IF NOT EXISTS money_source_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                money_source_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('expense', 'deposit', 'adjustment')),
                amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                expense_id INTEGER,
                note TEXT,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (money_source_id) REFERENCES money_sources(id),
                FOREIGN KEY (expense_id) REFERENCES expenses(id)
            );
        """)
        conn.commit()
    finally:
        close_connection(conn)
