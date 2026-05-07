"""
Repositorio de consultas analíticas bibliométricas.
Todas las consultas son de solo lectura (SELECT).
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from intellectclone.models.institucional import CuerpoAcademico, Dependencia
from intellectclone.models.persona import Persona
from intellectclone.models.produccion import Coautoria, Paper


class RepositorioAnalitica:
    """Consultas agregadas para los endpoints de analítica bibliométrica."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def papers_por_anio(self) -> list[dict[str, Any]]:
        """Serie temporal: papers agrupados por año con suma de citas."""
        stmt = (
            sa.select(
                Paper.año,
                sa.func.count(Paper.id).label("total_papers"),
                sa.func.coalesce(sa.func.sum(Paper.total_citas), 0).label("total_citas"),
            )
            .where(Paper.año.is_not(None))
            .group_by(Paper.año)
            .order_by(Paper.año)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def top_dependencias(self, limite: int = 10) -> list[dict[str, Any]]:
        """Top N dependencias por número de papers únicos de sus investigadores."""
        stmt = (
            sa.select(
                Dependencia.id.label("dependencia_id"),
                Dependencia.nombre,
                Dependencia.nombre_corto,
                sa.func.count(sa.func.distinct(Paper.id)).label("total_papers"),
                sa.func.count(sa.func.distinct(Persona.id)).label("total_personas"),
            )
            .join(Persona, Persona.dependencia_id == Dependencia.id)
            .join(Coautoria, Coautoria.persona_id == Persona.id)
            .join(Paper, Paper.id == Coautoria.paper_id)
            .where(Dependencia.activa == True)  # noqa: E712
            .group_by(Dependencia.id, Dependencia.nombre, Dependencia.nombre_corto)
            .order_by(sa.func.count(sa.func.distinct(Paper.id)).desc())
            .limit(limite)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def top_investigadores(
        self,
        limite: int = 10,
        orden: str = "papers",
    ) -> list[dict[str, Any]]:
        """Top N investigadores por papers cosechados o por citas totales."""
        n_papers_expr = sa.func.count(sa.func.distinct(Coautoria.paper_id))
        order_expr = n_papers_expr.desc() if orden == "papers" else Persona.total_citas.desc()

        stmt = (
            sa.select(
                Persona.id.label("persona_id"),
                Persona.nombre_completo,
                Persona.nivel_snii,
                n_papers_expr.label("n_papers_cosechados"),
                Persona.total_citas,
                Persona.indice_h,
            )
            .join(Coautoria, Coautoria.persona_id == Persona.id)
            .where(Persona.activa == True)  # noqa: E712
            .group_by(
                Persona.id,
                Persona.nombre_completo,
                Persona.nivel_snii,
                Persona.total_citas,
                Persona.indice_h,
            )
            .order_by(order_expr)
            .limit(limite)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def red_coautoria(
        self,
        persona_id: uuid.UUID | None = None,
        limite_nodos: int = 100,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Nodos + aristas para visualización de red de coautoría.
        Si persona_id es dado, devuelve la red ego de esa persona.
        """
        c1 = aliased(Coautoria, flat=True)
        c2 = aliased(Coautoria, flat=True)

        if persona_id is not None:
            # Red ego: papers de la persona + todos sus coautores
            subq_papers = (
                sa.select(Coautoria.paper_id)
                .where(Coautoria.persona_id == persona_id)
                .scalar_subquery()
            )
            personas_en_red = (
                sa.select(sa.func.distinct(Coautoria.persona_id))
                .where(Coautoria.paper_id.in_(subq_papers))
                .scalar_subquery()
            )
        else:
            # Red completa: todas las personas con coautoría
            personas_en_red = sa.select(sa.func.distinct(Coautoria.persona_id)).scalar_subquery()
            subq_papers = None

        # Nodos
        nodos_stmt = (
            sa.select(
                Persona.id.label("persona_id"),
                Persona.nombre_completo,
                Persona.dependencia_id,
                sa.func.count(sa.func.distinct(Coautoria.paper_id)).label("grado"),
            )
            .join(Coautoria, Coautoria.persona_id == Persona.id)
            .where(Persona.id.in_(personas_en_red))
            .group_by(Persona.id, Persona.nombre_completo, Persona.dependencia_id)
            .order_by(sa.func.count(sa.func.distinct(Coautoria.paper_id)).desc())
            .limit(limite_nodos)
        )
        nodos_result = await self._session.execute(nodos_stmt)
        nodos = [dict(r._mapping) for r in nodos_result.all()]

        # Aristas: pares de personas con coautoría (sin duplicados: a_id < b_id)
        ids_en_red = [n["persona_id"] for n in nodos]
        if not ids_en_red:
            return nodos, []

        aristas_stmt = (
            sa.select(
                c1.persona_id.label("persona_a_id"),
                c2.persona_id.label("persona_b_id"),
                sa.func.count(sa.func.distinct(c1.paper_id)).label("n_papers_comunes"),
            )
            .join(c2, c1.paper_id == c2.paper_id)
            .where(c1.persona_id < c2.persona_id)
            .where(c1.persona_id.in_(ids_en_red))
            .where(c2.persona_id.in_(ids_en_red))
            .group_by(c1.persona_id, c2.persona_id)
            .order_by(sa.func.count(sa.func.distinct(c1.paper_id)).desc())
        )
        aristas_result = await self._session.execute(aristas_stmt)
        aristas = [dict(r._mapping) for r in aristas_result.all()]

        return nodos, aristas

    async def estadisticas_globales(self) -> dict[str, int]:
        """Totales globales del sistema."""
        resultados: dict[str, int] = {}

        for nombre, stmt in [
            ("total_personas", sa.select(sa.func.count(Persona.id)).where(Persona.activa == True)),  # noqa: E712
            ("total_papers", sa.select(sa.func.count(Paper.id))),
            ("total_coautorias", sa.select(sa.func.count(Coautoria.id))),
            (
                "total_dependencias",
                sa.select(sa.func.count(Dependencia.id)).where(Dependencia.activa == True),  # noqa: E712
            ),
            (
                "total_cuerpos_academicos",
                sa.select(sa.func.count(CuerpoAcademico.id)).where(CuerpoAcademico.activo == True),  # noqa: E712
            ),
        ]:
            r = await self._session.execute(stmt)
            resultados[nombre] = int(r.scalar_one())

        return resultados
