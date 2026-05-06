"""
Base declarativa de SQLAlchemy para todos los modelos de IntellectClone.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):  # type: ignore[misc]
    """Clase base para todos los modelos ORM del sistema."""

    pass
