"""Engine, sesión y factory de SQLAlchemy."""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.get_database_url(),
    connect_args={"check_same_thread": False},
    echo=_settings.SQL_ECHO,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    """Habilita foreign keys en cada conexión nueva.

    SQLite los desactiva por defecto, lo que sería una incoherencia con el
    SQL crudo (que sí los activa). Esto los unifica.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI que provee una sesión y la cierra al terminar la request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
