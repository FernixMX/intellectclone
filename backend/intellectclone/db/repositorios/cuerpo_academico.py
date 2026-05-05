"""
Repositorio para la entidad CuerpoAcademico.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db.repositorios.base import RepositorioBase
from intellectclone.models.institucional import CuerpoAcademico


class RepositorioCuerpoAcademico(RepositorioBase[CuerpoAcademico]):
    """Repositorio especializado para operaciones con CuerpoAcademico."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CuerpoAcademico)

    async def listar_por_dependencia(
        self,
        dependencia_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[int, list[CuerpoAcademico]]:
        """Lista cuerpos académicos, opcionalmente filtrados por dependencia."""
        stmt = select(CuerpoAcademico).where(CuerpoAcademico.activo == True)  # noqa: E712

        if dependencia_id is not None:
            stmt = stmt.where(CuerpoAcademico.dependencia_id == dependencia_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(CuerpoAcademico.nombre).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return total, items
