"""Modelos ORM (SQLAlchemy / equivalente JPA en Python).

Nota: importar todos los modelos aquí asegura que estén registrados en
`Base.metadata` cuando los tests ejecuten `Base.metadata.create_all()`.
"""

from app.db.models.money_source_model import MoneySource
from app.db.models.user_model import User

__all__ = ["MoneySource", "User"]
