"""
Endpoints de analítica bibliométrica.

GET /api/v1/analitica/papers-por-año
GET /api/v1/analitica/top-dependencias
GET /api/v1/analitica/top-investigadores
GET /api/v1/analitica/red-coautoria
GET /api/v1/analitica/estadisticas-globales
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db import get_db
from intellectclone.db.repositorios.analitica import RepositorioAnalitica
from intellectclone.schemas.analitica import (
    AristaCoautoria,
    EstadisticasGlobalesResponse,
    NodoCoautoria,
    PuntoPapersPorAnio,
    RedCoautoriaResponse,
    SerieTemporalPapersResponse,
    TopDependenciaItem,
    TopDependenciasResponse,
    TopInvestigadoresResponse,
    TopInvestigadorItem,
)

router = APIRouter(prefix="/analitica", tags=["analitica"])


@router.get(  # type: ignore[misc]
    "/papers-por-año",
    response_model=SerieTemporalPapersResponse,
    summary="Serie temporal de papers por año de publicación",
)
async def papers_por_anio(
    session: AsyncSession = Depends(get_db),
) -> SerieTemporalPapersResponse:
    """Devuelve el conteo de papers y citas agrupados por año, ordenado cronológicamente."""
    repo = RepositorioAnalitica(session)
    datos = await repo.papers_por_anio()
    puntos = [PuntoPapersPorAnio(**d) for d in datos]
    total_historico = sum(p.total_papers for p in puntos)
    return SerieTemporalPapersResponse(datos=puntos, total_papers_historico=total_historico)


@router.get(  # type: ignore[misc]
    "/top-dependencias",
    response_model=TopDependenciasResponse,
    summary="Top dependencias de la UAT por número de papers",
)
async def top_dependencias(
    limite: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> TopDependenciasResponse:
    """Devuelve las N dependencias con más papers publicados por sus investigadores."""
    repo = RepositorioAnalitica(session)
    datos = await repo.top_dependencias(limite=limite)
    return TopDependenciasResponse(items=[TopDependenciaItem(**d) for d in datos])


@router.get(  # type: ignore[misc]
    "/top-investigadores",
    response_model=TopInvestigadoresResponse,
    summary="Top investigadores de la UAT por producción o citaciones",
)
async def top_investigadores(
    limite: int = Query(default=10, ge=1, le=50),
    orden: str = Query(default="papers", pattern="^(papers|citas)$"),
    session: AsyncSession = Depends(get_db),
) -> TopInvestigadoresResponse:
    """
    Devuelve los N investigadores con mayor producción.
    `orden=papers` ordena por número de papers cosechados.
    `orden=citas` ordena por total de citas.
    """
    repo = RepositorioAnalitica(session)
    datos = await repo.top_investigadores(limite=limite, orden=orden)
    return TopInvestigadoresResponse(items=[TopInvestigadorItem(**d) for d in datos])


@router.get(  # type: ignore[misc]
    "/red-coautoria",
    response_model=RedCoautoriaResponse,
    summary="Red de coautoría (nodos + aristas) para visualización",
)
async def red_coautoria(
    persona_id: uuid.UUID | None = Query(default=None),
    dependencia_id: uuid.UUID | None = Query(default=None),
    limite_nodos: int = Query(default=100, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
) -> RedCoautoriaResponse:
    """
    Devuelve la red de coautoría como lista de nodos (investigadores) y aristas (colaboraciones).
    - dependencia_id: todos los investigadores de esa dependencia + coautores externos.
    - persona_id: red ego de esa persona.
    - (ninguno): top N más productivos global.
    """
    repo = RepositorioAnalitica(session)
    nodos_raw, aristas_raw = await repo.red_coautoria(
        persona_id=persona_id, dependencia_id=dependencia_id, limite_nodos=limite_nodos
    )
    nodos = [NodoCoautoria(**n) for n in nodos_raw]
    aristas = [AristaCoautoria(**a) for a in aristas_raw]
    return RedCoautoriaResponse(
        nodos=nodos,
        aristas=aristas,
        total_nodos=len(nodos),
        total_aristas=len(aristas),
    )


@router.get(  # type: ignore[misc]
    "/conceptos-frecuentes",
    response_model=list[str],
    summary="Top conceptos/áreas de investigación por frecuencia en papers",
)
async def conceptos_frecuentes(
    limite: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> list[str]:
    """Devuelve los N conceptos más frecuentes en toda la colección de papers."""
    repo = RepositorioAnalitica(session)
    return await repo.conceptos_frecuentes(limite=limite)


@router.get(  # type: ignore[misc]
    "/estadisticas-globales",
    response_model=EstadisticasGlobalesResponse,
    summary="Totales globales del sistema (personas, papers, coautorias, dependencias)",
)
async def estadisticas_globales(
    session: AsyncSession = Depends(get_db),
) -> EstadisticasGlobalesResponse:
    """Devuelve los conteos totales del sistema sin filtros."""
    repo = RepositorioAnalitica(session)
    datos = await repo.estadisticas_globales()
    return EstadisticasGlobalesResponse(**datos)
