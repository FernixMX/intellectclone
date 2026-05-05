"""
Repositorio para la entidad Dependencia.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db.repositorios.base import RepositorioBase
from intellectclone.models.institucional import Dependencia


class RepositorioDependencia(RepositorioBase[Dependencia]):
    """Repositorio especializado para operaciones con Dependencia."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Dependencia)
