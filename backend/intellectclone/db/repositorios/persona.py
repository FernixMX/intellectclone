"""
Repositorio para la entidad Persona.
"""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from intellectclone.db.repositorios.base import RepositorioBase
from intellectclone.models.enums import NivelSnii, TipoPersona
from intellectclone.models.persona import Persona


class RepositorioPersona(RepositorioBase[Persona]):
    """Repositorio especializado para operaciones con Persona."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Persona)

    async def listar_con_filtros(
        self,
        tipo: TipoPersona | None = None,
        dependencia_id: uuid.UUID | None = None,
        cuerpo_academico_id: uuid.UUID | None = None,
        nivel_snii: NivelSnii | None = None,
        tiene_gemelo_validado: bool | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[int, list[Persona]]:
        """
        Lista personas con filtros dinámicos.
        Devuelve (total, items).
        """
        stmt = select(Persona).where(Persona.activa == True)  # noqa: E712

        if tipo is not None:
            stmt = stmt.where(Persona.tipo == tipo)
        if dependencia_id is not None:
            stmt = stmt.where(Persona.dependencia_id == dependencia_id)
        if cuerpo_academico_id is not None:
            stmt = stmt.where(Persona.cuerpo_academico_id == cuerpo_academico_id)
        if nivel_snii is not None:
            stmt = stmt.where(Persona.nivel_snii == nivel_snii)
        if q is not None:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Persona.nombre_completo.ilike(pattern),
                    Persona.nombre_normalizado.ilike(pattern),
                )
            )
        if tiene_gemelo_validado is not None:
            # Filtra si tiene al menos un gemelo en estado validado o publicado
            from intellectclone.models.enums import EstadoGemelo
            from intellectclone.models.gemelo import Gemelo

            estados_validos = [EstadoGemelo.validado, EstadoGemelo.publicado]
            subq = (
                select(Gemelo.persona_id)
                .where(Gemelo.estado.in_(estados_validos))
                .where(Gemelo.es_version_actual == True)  # noqa: E712
                .scalar_subquery()
            )
            if tiene_gemelo_validado:
                stmt = stmt.where(Persona.id.in_(subq))
            else:
                stmt = stmt.where(Persona.id.not_in(subq))

        # Contar total con los filtros aplicados
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginación y orden
        stmt = stmt.order_by(Persona.nombre_completo).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return total, items

    async def obtener_con_relaciones(self, id: uuid.UUID) -> Persona | None:
        """
        Obtiene una Persona con sus relaciones principales pre-cargadas:
        dependencia, cuerpo_academico, y gemelos actuales.
        """
        stmt = (
            select(Persona)
            .options(
                selectinload(Persona.dependencia),
                selectinload(Persona.cuerpo_academico),
                selectinload(Persona.gemelos),
            )
            .where(Persona.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[return-value]
