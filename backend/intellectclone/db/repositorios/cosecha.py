"""
Repositorio de cosechas — operaciones de persistencia para el modelo Cosecha.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db.repositorios.base import RepositorioBase
from intellectclone.models.enums import EstadoCosecha, TipoFuente
from intellectclone.models.sistema import Cosecha


class RepositorioCosecha(RepositorioBase[Cosecha]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cosecha)

    async def listar_con_filtros(
        self,
        fuente: TipoFuente | None = None,
        estado: EstadoCosecha | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[int, list[Cosecha]]:
        stmt = select(Cosecha)

        if fuente is not None:
            stmt = stmt.where(Cosecha.fuente == fuente)
        if estado is not None:
            stmt = stmt.where(Cosecha.estado == estado)
        if desde is not None:
            stmt = stmt.where(Cosecha.created_at >= desde)
        if hasta is not None:
            stmt = stmt.where(Cosecha.created_at <= hasta)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Cosecha.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return total, items

    async def obtener_ultima_por_fuente(self, fuente: TipoFuente) -> Cosecha | None:
        stmt = (
            select(Cosecha)
            .where(Cosecha.fuente == fuente)
            .order_by(Cosecha.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def crear_cosecha(
        self,
        fuente: TipoFuente,
        modo: str,
        parametros: dict,  # type: ignore[type-arg]
        configuracion: dict,  # type: ignore[type-arg]
        disparada_por: uuid.UUID | None,
    ) -> Cosecha:
        cosecha = Cosecha(
            fuente=fuente,
            estado=EstadoCosecha.programada,
            disparada_manual=True,
            disparada_por=disparada_por,
            configuracion={
                "modo": modo,
                "parametros": parametros,
                **configuracion,
            },
        )
        self._session.add(cosecha)
        await self._session.flush()
        await self._session.refresh(cosecha)
        return cosecha
