"""
Desambiguador de autores para el pipeline de cosecha.

Implementa la cascada: ORCID → OpenAlex Author ID → fuzzy nombre + dependencia.
Devuelve una decisión; la creación de nuevas personas queda en el caller.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.harvesters.normalizer import normalizar_nombre, ratio_similitud
from intellectclone.models.persona import Persona

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

ROR_UAT = "https://ror.org/00qm7vk32"

_UMBRAL_CONFIABLE = 0.95
_UMBRAL_REVISION = 0.85


@dataclass
class ResultadoDesambiguacion:
    """Decisión del desambiguador para un authorship dado."""

    metodo: str
    confianza: float
    persona_id: uuid.UUID | None = None
    requiere_revision: bool = False
    candidato_revision_id: uuid.UUID | None = None
    datos_orcid_actualizar: dict[str, Any] = field(default_factory=dict)


async def desambiguar_autor(
    authorship: dict[str, Any],
    session: AsyncSession,
) -> ResultadoDesambiguacion:
    """
    Recibe un authorship (formato OpenAlex) y devuelve la decisión de match.

    Niveles de confianza:
    1. ORCID exacto              → confianza 1.0, usar existente
    2. OpenAlex Author ID exacto → confianza 0.95, usar existente
    3. Fuzzy nombre + institución→ confianza variable
       - ≥ 0.95 → usar existente
       - 0.85–0.95 → marcar para revisión, no asignar
       - < 0.85 → persona nueva
    """
    author_data: dict[str, Any] = authorship.get("author") or {}
    orcid_raw: str | None = author_data.get("orcid")
    openalex_author_id: str | None = _extraer_openalex_author_id(author_data)
    nombre_display: str = author_data.get("display_name") or ""
    instituciones: list[dict[str, Any]] = authorship.get("institutions") or []

    # ------------------------------------------------------------------
    # Nivel 1: ORCID
    # ------------------------------------------------------------------
    if orcid_raw:
        orcid_limpio = _limpiar_orcid(orcid_raw)
        resultado = await _buscar_por_orcid(orcid_limpio, session)
        if resultado is not None:
            extra: dict[str, Any] = {}
            if openalex_author_id and not resultado.openalex_id:
                extra["openalex_id"] = openalex_author_id
            logger.debug(
                "desambiguador.match_orcid",
                persona_id=str(resultado.id),
                orcid=orcid_limpio,
            )
            return ResultadoDesambiguacion(
                metodo="orcid",
                confianza=1.0,
                persona_id=resultado.id,
                datos_orcid_actualizar=extra,
            )

    # ------------------------------------------------------------------
    # Nivel 2: OpenAlex Author ID
    # ------------------------------------------------------------------
    if openalex_author_id:
        resultado = await _buscar_por_openalex_id(openalex_author_id, session)
        if resultado is not None:
            extra_orcid: dict[str, Any] = {}
            if orcid_raw and not resultado.orcid:
                extra_orcid["orcid"] = _limpiar_orcid(orcid_raw)
            logger.debug(
                "desambiguador.match_openalex_id",
                persona_id=str(resultado.id),
                openalex_author_id=openalex_author_id,
            )
            return ResultadoDesambiguacion(
                metodo="openalex_id",
                confianza=0.95,
                persona_id=resultado.id,
                datos_orcid_actualizar=extra_orcid,
            )

    # ------------------------------------------------------------------
    # Nivel 3: Fuzzy nombre + boost por institución UAT
    # ------------------------------------------------------------------
    if not nombre_display:
        return ResultadoDesambiguacion(metodo="nuevo", confianza=0.0)

    nombre_norm = normalizar_nombre(nombre_display)
    candidatos = await _buscar_candidatos_nombre(nombre_norm, session)

    mejor: Persona | None = None
    mejor_score = 0.0
    comparte_uat = _autor_en_uat(instituciones)

    for cand in candidatos:
        score = ratio_similitud(nombre_norm, cand.nombre_normalizado)
        if comparte_uat and cand.dependencia_id is not None:
            score = min(1.0, score + 0.05)
        if score > mejor_score:
            mejor = cand
            mejor_score = score

    if mejor is not None and mejor_score >= _UMBRAL_CONFIABLE:
        logger.debug(
            "desambiguador.match_fuzzy_confiable",
            persona_id=str(mejor.id),
            score=mejor_score,
        )
        return ResultadoDesambiguacion(
            metodo="fuzzy",
            confianza=mejor_score,
            persona_id=mejor.id,
        )

    if mejor is not None and mejor_score >= _UMBRAL_REVISION:
        logger.info(
            "desambiguador.match_fuzzy_revision",
            candidato_id=str(mejor.id),
            score=mejor_score,
            nombre=nombre_display,
        )
        return ResultadoDesambiguacion(
            metodo="revision_pendiente",
            confianza=mejor_score,
            persona_id=None,
            requiere_revision=True,
            candidato_revision_id=mejor.id,
        )

    return ResultadoDesambiguacion(metodo="nuevo", confianza=0.0)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _limpiar_orcid(orcid: str) -> str:
    return orcid.replace("https://orcid.org/", "").strip()


def _extraer_openalex_author_id(author_data: dict[str, Any]) -> str | None:
    raw_id: str = author_data.get("id") or ""
    parte = raw_id.split("/")[-1]
    return parte if parte else None


def _autor_en_uat(instituciones: list[dict[str, Any]]) -> bool:
    return any(inst.get("ror") == ROR_UAT for inst in instituciones)


async def _buscar_por_orcid(orcid: str, session: AsyncSession) -> Persona | None:
    stmt = select(Persona).where(Persona.orcid == orcid)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def _buscar_por_openalex_id(openalex_id: str, session: AsyncSession) -> Persona | None:
    stmt = select(Persona).where(Persona.openalex_id == openalex_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def _buscar_candidatos_nombre(nombre_norm: str, session: AsyncSession) -> list[Persona]:
    """
    Recupera candidatos usando el operador pg_trgm `%` (similitud ≥ 0.3 por default).
    En tests, esta función se mockea para devolver candidatos predefinidos.
    """
    stmt = select(Persona).where(Persona.nombre_normalizado.op("%")(nombre_norm))
    result = await session.execute(stmt)
    return list(result.scalars().all())
