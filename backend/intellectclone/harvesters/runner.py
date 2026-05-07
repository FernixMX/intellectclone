"""
Runner de cosechadores: registro global y orquestación de una sesión de cosecha.

Uso:
    registrar_harvester(TipoFuente.openalex, OpenAlexHarvester)
    await ejecutar_cosecha(cosecha_id, TipoFuente.openalex, modo, parametros, session)
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
from typing import Any

import structlog
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.tipos import AccionIntento, NivelError, ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPersona
from intellectclone.models.persona import Persona
from intellectclone.models.produccion import Coautoria, Paper

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_REGISTRY: dict[str, type[BaseHarvester]] = {}

_BATCH_SIZE = 100


def registrar_harvester(fuente_tipo: str, clase: type[BaseHarvester]) -> None:
    """Registra una clase harvester para el tipo de fuente dado."""
    _REGISTRY[fuente_tipo] = clase
    logger.debug("harvester.registrado", fuente_tipo=fuente_tipo, clase=clase.__name__)


def obtener_harvester(fuente_tipo: str) -> type[BaseHarvester]:
    """Devuelve la clase harvester para el tipo dado. KeyError si no existe."""
    if fuente_tipo not in _REGISTRY:
        raise KeyError(f"No hay harvester registrado para fuente_tipo='{fuente_tipo}'")
    return _REGISTRY[fuente_tipo]


async def ejecutar_cosecha(
    cosecha_id: str,
    fuente_tipo: str,
    modo: str,
    parametros: dict[str, Any],
    config: dict[str, Any],
    session: AsyncSession,
    *,
    max_errores_consecutivos: int = 10,
) -> dict[str, Any]:
    """
    Orquesta una sesión de cosecha completa para el fuente_tipo dado.

    Cada registro se envuelve en un SAVEPOINT individual para que un error
    de integridad (DOI/ORCID duplicado) solo descarte ese registro, sin
    hacer rollback del batch completo.
    """
    clase = obtener_harvester(fuente_tipo)
    harvester = clase()
    harvester.configurar(config)

    log = logger.bind(cosecha_id=cosecha_id, fuente_tipo=fuente_tipo, modo=modo)
    log.info("cosecha.inicio")

    total = 0
    nuevos = 0
    errores = 0
    errores_consecutivos = 0

    try:
        async for resultado in harvester.cosechar(cosecha_id, modo, parametros):
            try:
                async with session.begin_nested():
                    es_nuevo = await _persistir_resultado(resultado, session, cosecha_id)
                total += 1
                if es_nuevo:
                    nuevos += 1
                errores_consecutivos = 0

                if resultado.advertencias:
                    log.warning(
                        "cosecha.advertencias_registro",
                        fuente_id=resultado.fuente_id,
                        advertencias=resultado.advertencias,
                    )

                if total % _BATCH_SIZE == 0:
                    await session.commit()
                    log.debug("cosecha.batch_commit", total=total)

            except IntegrityError as exc:
                errores += 1
                log.warning(
                    "cosecha.integridad_saltada",
                    fuente_id=resultado.fuente_id,
                    error=str(getattr(exc, "orig", exc)),
                )
            except Exception as exc:
                errores += 1
                errores_consecutivos += 1
                log.error(
                    "cosecha.error_registro",
                    fuente_id=resultado.fuente_id,
                    error=str(exc),
                )
                if errores_consecutivos >= max_errores_consecutivos:
                    await _registrar_error_en_cosecha(
                        session, cosecha_id, str(exc), NivelError.critical
                    )
                    log.error(
                        "cosecha.abortada_por_errores",
                        errores_consecutivos=errores_consecutivos,
                    )
                    raise

        await session.commit()

    except Exception as exc:
        await session.rollback()

        contexto: dict[str, Any] = {"cosecha_id": cosecha_id, "fuente_tipo": fuente_tipo}
        decision = harvester.manejar_error(exc, contexto, errores_consecutivos)

        if decision.accion == AccionIntento.abortar:
            await _registrar_error_en_cosecha(session, cosecha_id, str(exc), NivelError.critical)
            log.error("cosecha.abortada", razon=decision.mensaje)
            raise

        if decision.accion == AccionIntento.reintentar:
            log.info("cosecha.esperando_reintento", delay=decision.delay_segundos)
            await asyncio.sleep(decision.delay_segundos)

        await _registrar_error_en_cosecha(session, cosecha_id, str(exc), NivelError.error)

    resumen: dict[str, Any] = {
        "cosecha_id": cosecha_id,
        "fuente_tipo": fuente_tipo,
        "total": total,
        "nuevos": nuevos,
        "errores": errores,
    }
    log.info("cosecha.fin", **resumen)
    return resumen


async def _persistir_resultado(
    resultado: ResultadoCosecha,
    session: AsyncSession,
    cosecha_id: str,
) -> bool:
    """
    Upsert Paper + Persona + Coautoria para un resultado de cosecha.

    Para conflictos de DOI (paper) u ORCID (persona), reintenta sin ese campo
    dentro de un savepoint anidado para no perder el registro.
    """
    datos = resultado.datos

    openalex_id: str | None = str(datos.get("openalex_id") or "").strip() or None
    titulo: str = str(datos.get("titulo") or "").strip()
    if not titulo:
        return False

    fecha_pub_raw = datos.get("fecha_publicacion")
    if isinstance(fecha_pub_raw, str):
        try:
            fecha_pub: date | None = date.fromisoformat(fecha_pub_raw)
        except ValueError:
            fecha_pub = None
    else:
        fecha_pub = fecha_pub_raw

    doi: str | None = datos.get("doi")

    paper_db_id, is_nuevo = await _upsert_paper(
        session=session,
        openalex_id=openalex_id,
        doi=doi,
        titulo=titulo,
        fecha_pub=fecha_pub,
        datos=datos,
        cosecha_id=cosecha_id,
    )
    if paper_db_id is None:
        return False

    autorships: list[dict[str, Any]] = list(datos.get("autorships") or [])
    for idx, authorship in enumerate(autorships):
        author: dict[str, Any] = authorship.get("author") or {}
        author_oa_raw: str = str(author.get("id") or "").strip()
        author_oa_id: str | None = _short_id(author_oa_raw) if author_oa_raw else None

        display_name: str = str(author.get("display_name") or "").strip()
        if not display_name:
            continue

        orcid_raw: str = str(author.get("orcid") or "").strip()
        orcid: str | None = orcid_raw.split("orcid.org/")[-1].strip() or None if orcid_raw else None

        position: str = str(authorship.get("author_position") or "middle")
        raw_aff_raw = authorship.get("raw_affiliation_string") or authorship.get(
            "raw_affiliation_strings"
        )
        if isinstance(raw_aff_raw, list):
            raw_aff: str | None = "; ".join(str(x) for x in raw_aff_raw)[:500] or None
        else:
            raw_aff = str(raw_aff_raw or "")[:500] or None

        persona_id = await _upsert_persona(
            session=session,
            author_oa_id=author_oa_id,
            display_name=display_name,
            orcid=orcid,
        )
        if persona_id is None:
            continue

        coautoria_stmt = pg_insert(Coautoria).values(
            id=uuid.uuid4(),
            persona_id=persona_id,
            paper_id=paper_db_id,
            posicion=idx + 1,
            total_autores=len(autorships),
            es_primer_autor=position == "first",
            es_ultimo_autor=position == "last",
            es_autor_correspondiente=False,
            afiliacion_declarada=raw_aff,
            confianza_match=1.0,
            metodo_match="openalex",
        )
        await session.execute(coautoria_stmt.on_conflict_do_nothing())

    return is_nuevo


async def _upsert_paper(
    *,
    session: AsyncSession,
    openalex_id: str | None,
    doi: str | None,
    titulo: str,
    fecha_pub: date | None,
    datos: dict[str, Any],
    cosecha_id: str,
) -> tuple[uuid.UUID | None, bool]:
    """Upsert Paper. Si hay conflicto de DOI, reintenta sin DOI."""

    def _build_stmt(use_doi: str | None) -> Any:
        ins = pg_insert(Paper).values(
            id=uuid.uuid4(),
            openalex_id=openalex_id,
            doi=use_doi,
            titulo=titulo,
            titulo_normalizado=datos.get("titulo_normalizado"),
            abstract_texto=datos.get("abstract_texto"),
            año=datos.get("año"),
            fecha_publicacion=fecha_pub,
            idioma=datos.get("idioma"),
            revista=datos.get("revista"),
            issn=datos.get("issn"),
            editorial=datos.get("editorial"),
            volumen=datos.get("volumen"),
            numero=datos.get("numero"),
            paginas=datos.get("paginas"),
            open_access=datos.get("open_access"),
            url_pdf=datos.get("url_pdf"),
            url_landing=datos.get("url_landing"),
            total_citas=int(datos.get("total_citas") or 0),
            citas_por_año=datos.get("citas_por_año"),
            conceptos=datos.get("conceptos"),
            tipo=datos.get("tipo", "otro"),
            fuente_origen=TipoFuente.openalex.value,
            cosecha_id=uuid.UUID(cosecha_id),
            metadatos={},
        )
        if openalex_id:
            return ins.on_conflict_do_update(
                index_elements=["openalex_id"],
                set_={
                    "titulo": ins.excluded.titulo,
                    "abstract_texto": ins.excluded.abstract_texto,
                    "total_citas": ins.excluded.total_citas,
                    "citas_por_año": ins.excluded.citas_por_año,
                    "url_pdf": ins.excluded.url_pdf,
                    "url_landing": ins.excluded.url_landing,
                    "open_access": ins.excluded.open_access,
                    "updated_at": func.now(),
                },
            ).returning(Paper.id, Paper.created_at, Paper.updated_at)
        return ins.on_conflict_do_nothing().returning(Paper.id, Paper.created_at, Paper.updated_at)

    try:
        async with session.begin_nested():
            row = (await session.execute(_build_stmt(doi))).first()
    except IntegrityError:
        # DOI conflict with a different paper: retry without DOI
        row = (await session.execute(_build_stmt(None))).first()

    if row is None:
        return None, False
    return row[0], row[1] == row[2]


async def _upsert_persona(
    *,
    session: AsyncSession,
    author_oa_id: str | None,
    display_name: str,
    orcid: str | None,
) -> uuid.UUID | None:
    """Upsert Persona. Si hay conflicto de ORCID, reintenta sin ORCID."""

    def _build_stmt(use_orcid: str | None) -> Any:
        values: dict[str, Any] = {
            "id": uuid.uuid4(),
            "nombre_completo": display_name,
            "nombre_normalizado": display_name.lower(),
            "tipo": TipoPersona.investigador.value,
            "fuente_principal": TipoFuente.openalex.value,
            "metadatos": {},
        }
        if author_oa_id:
            values["openalex_id"] = author_oa_id
        if use_orcid:
            values["orcid"] = use_orcid

        ins = pg_insert(Persona).values(**values)
        if author_oa_id:
            return ins.on_conflict_do_update(
                index_elements=["openalex_id"],
                set_={"nombre_completo": ins.excluded.nombre_completo},
            ).returning(Persona.id)
        return ins.on_conflict_do_nothing().returning(Persona.id)

    try:
        async with session.begin_nested():
            row = (await session.execute(_build_stmt(orcid))).scalar()
    except IntegrityError:
        # ORCID conflict: retry without ORCID
        row = (await session.execute(_build_stmt(None))).scalar()

    return uuid.UUID(str(row)) if row is not None else None


def _short_id(url: str) -> str | None:
    """Extrae ID corto de URL OpenAlex, ej. 'W1234' de 'https://openalex.org/W1234'."""
    part = url.rstrip("/").split("/")[-1].strip()
    return part if part else None


async def _registrar_error_en_cosecha(
    session: AsyncSession,
    cosecha_id: str,
    mensaje: str,
    nivel: NivelError,
) -> None:
    """Persiste un evento de error en la tabla log_cosecha (stub para C4+)."""
    logger.log(
        nivel.value,
        "cosecha.error_registrado",
        cosecha_id=cosecha_id,
        mensaje=mensaje,
    )
    _ = session
