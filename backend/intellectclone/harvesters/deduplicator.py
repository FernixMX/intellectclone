"""
Deduplicador de papers para el pipeline de cosecha.

Cascada: DOI → OpenAlex ID → Handle RIUAT → fuzzy título+año+primer autor.
Prioridad de fuentes para consolidación: OpenAlex > Crossref > VuFind > RIUAT > manual.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.harvesters.normalizer import (
    normalizar_doi,
    normalizar_nombre,
    normalizar_titulo,
    ratio_similitud,
)
from intellectclone.models.enums import TipoFuente
from intellectclone.models.produccion import Paper

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_UMBRAL_DEDUP_AUTO = 0.95
_UMBRAL_DEDUP_REVISION = 0.85

_PRIORIDAD_FUENTE: dict[str | None, int] = {
    TipoFuente.openalex: 5,
    TipoFuente.crossref: 4,
    TipoFuente.vufind_uat: 3,
    TipoFuente.riuat: 2,
    TipoFuente.snii_uat: 1,
    TipoFuente.manual: 0,
    None: -1,
}


@dataclass
class ResultadoDeduplicacion:
    """Decisión del deduplicador para un paper nuevo."""

    es_duplicado: bool
    metodo: str
    paper_id: uuid.UUID | None = None
    requiere_revision: bool = False
    score: float = 0.0
    fuentes_secundarias: list[str] = field(default_factory=list)


async def deduplicar_paper(
    paper_nuevo: dict[str, Any],
    session: AsyncSession,
) -> ResultadoDeduplicacion:
    """
    Determina si paper_nuevo ya existe en la base.

    Cuando es duplicado, consolida metadatos en el existente y devuelve su ID.
    Cuando score está en zona gris (0.85-0.95), marca para revisión humana.
    """
    # ------------------------------------------------------------------
    # Nivel 1: DOI
    # ------------------------------------------------------------------
    doi_raw: str | None = paper_nuevo.get("doi")
    if doi_raw:
        doi_norm = normalizar_doi(doi_raw)
        existente = await _buscar_por_doi(doi_norm, session)
        if existente is not None:
            fuente_nueva = paper_nuevo.get("fuente_origen")
            _consolidar_metadatos(existente, paper_nuevo)
            logger.debug("deduplicador.match_doi", paper_id=str(existente.id), doi=doi_norm)
            return ResultadoDeduplicacion(
                es_duplicado=True,
                metodo="doi",
                paper_id=existente.id,
                fuentes_secundarias=[fuente_nueva] if fuente_nueva else [],
            )

    # ------------------------------------------------------------------
    # Nivel 2: OpenAlex ID
    # ------------------------------------------------------------------
    openalex_id: str | None = paper_nuevo.get("openalex_id")
    if openalex_id:
        existente = await _buscar_por_openalex_id(openalex_id, session)
        if existente is not None:
            _consolidar_metadatos(existente, paper_nuevo)
            logger.debug("deduplicador.match_openalex_id", paper_id=str(existente.id))
            return ResultadoDeduplicacion(
                es_duplicado=True,
                metodo="openalex_id",
                paper_id=existente.id,
            )

    # ------------------------------------------------------------------
    # Nivel 3: Handle RIUAT
    # ------------------------------------------------------------------
    handle: str | None = paper_nuevo.get("handle_riuat")
    if handle:
        existente = await _buscar_por_handle(handle, session)
        if existente is not None:
            _consolidar_metadatos(existente, paper_nuevo)
            logger.debug("deduplicador.match_handle_riuat", paper_id=str(existente.id))
            return ResultadoDeduplicacion(
                es_duplicado=True,
                metodo="handle_riuat",
                paper_id=existente.id,
            )

    # ------------------------------------------------------------------
    # Nivel 4: Fuzzy título + año + primer autor
    # ------------------------------------------------------------------
    titulo_raw: str = paper_nuevo.get("titulo") or ""
    año: int | None = paper_nuevo.get("año")
    primer_autor: str = _obtener_primer_autor(paper_nuevo)

    if titulo_raw and año and primer_autor:
        titulo_norm = normalizar_titulo(titulo_raw)
        candidatos = await _buscar_candidatos_titulo(titulo_norm, año, session)

        for cand in candidatos:
            titulo_cand = cand.titulo_normalizado or normalizar_titulo(cand.titulo)
            sim = ratio_similitud(titulo_norm, titulo_cand)

            if sim >= _UMBRAL_DEDUP_AUTO:
                primer_autor_cand = _obtener_primer_autor_de_paper(cand)
                if _nombres_coinciden(primer_autor, primer_autor_cand):
                    _consolidar_metadatos(cand, paper_nuevo)
                    logger.debug(
                        "deduplicador.match_fuzzy",
                        paper_id=str(cand.id),
                        score=sim,
                    )
                    return ResultadoDeduplicacion(
                        es_duplicado=True,
                        metodo="fuzzy",
                        paper_id=cand.id,
                        score=sim,
                    )

            elif sim >= _UMBRAL_DEDUP_REVISION:
                logger.info(
                    "deduplicador.revision_pendiente",
                    candidato_id=str(cand.id),
                    score=sim,
                    titulo=titulo_raw[:80],
                )
                return ResultadoDeduplicacion(
                    es_duplicado=False,
                    metodo="revision_pendiente",
                    paper_id=None,
                    requiere_revision=True,
                    score=sim,
                )

    return ResultadoDeduplicacion(es_duplicado=False, metodo="nuevo")


def _consolidar_metadatos(existente: Paper, nuevo: dict[str, Any]) -> None:
    """
    Enriquece el paper existente con campos del nuevo que estén vacíos.
    Cuando ambos tienen valor, gana la fuente de mayor prioridad.
    """
    fuente_nueva_str: str | None = nuevo.get("fuente_origen")
    fuente_nueva = TipoFuente(fuente_nueva_str) if fuente_nueva_str else None
    fuente_existente = existente.fuente_origen

    prioridad_nueva = _PRIORIDAD_FUENTE.get(fuente_nueva, -1)
    prioridad_existente = _PRIORIDAD_FUENTE.get(fuente_existente, -1)
    nueva_gana = prioridad_nueva > prioridad_existente

    campos_simples: list[str] = ["doi", "abstract", "url_pdf", "titulo_normalizado"]
    for campo in campos_simples:
        valor_existente = getattr(existente, campo, None)
        valor_nuevo = nuevo.get(campo)
        if (
            valor_existente is None
            and valor_nuevo is not None
            or valor_existente is not None
            and valor_nuevo is not None
            and nueva_gana
        ):
            setattr(existente, campo, valor_nuevo)

    metadatos: dict[str, Any] = existente.metadatos or {}
    fuentes: list[str] = metadatos.get("fuentes_secundarias") or []
    if fuente_nueva_str and fuente_nueva_str not in fuentes:
        fuentes.append(fuente_nueva_str)
    metadatos["fuentes_secundarias"] = fuentes
    existente.metadatos = metadatos


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _obtener_primer_autor(paper: dict[str, Any]) -> str:
    autorships: list[dict[str, Any]] = paper.get("autorships") or paper.get("autores") or []
    if not autorships:
        return ""
    autor_data: dict[str, Any] = autorships[0].get("author") or autorships[0]
    nombre: str = autor_data.get("display_name") or autor_data.get("nombre") or ""
    return normalizar_nombre(nombre)


def _obtener_primer_autor_de_paper(paper: Paper) -> str:
    coautorias = paper.coautorias
    if not coautorias:
        return ""
    primera = sorted(coautorias, key=lambda c: c.orden or 0)[0]
    persona = primera.persona
    if persona is None:
        return ""
    nombre: str = persona.nombre_normalizado
    return nombre


def _nombres_coinciden(a: str, b: str, umbral: float = 0.85) -> bool:
    return ratio_similitud(a, b) >= umbral


async def _buscar_por_doi(doi: str, session: AsyncSession) -> Paper | None:
    result = await session.execute(select(Paper).where(Paper.doi == doi))
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def _buscar_por_openalex_id(openalex_id: str, session: AsyncSession) -> Paper | None:
    result = await session.execute(select(Paper).where(Paper.openalex_id == openalex_id))
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def _buscar_por_handle(handle: str, session: AsyncSession) -> Paper | None:
    result = await session.execute(select(Paper).where(Paper.handle_riuat == handle))
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def _buscar_candidatos_titulo(
    titulo_norm: str, año: int, session: AsyncSession
) -> list[Paper]:
    """
    Recupera candidatos filtrando por año y similitud pg_trgm sobre titulo_normalizado.
    En tests se mockea esta función para devolver candidatos predefinidos.
    """
    stmt = select(Paper).where(
        Paper.año == año,
        Paper.titulo_normalizado.op("%")(titulo_norm),
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
