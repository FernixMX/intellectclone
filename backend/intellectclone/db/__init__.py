"""
Capa de base de datos de IntellectClone.
Exporta los componentes principales para uso en otros módulos.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db.base import Base
from intellectclone.db.session import get_db

__all__ = ["AsyncSession", "Base", "get_db"]
