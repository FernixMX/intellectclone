"""
Runner de cosechadores: registro global y orquestación de una sesión de cosecha.

Uso:
    registrar_harvester(TipoFuente.openalex, OpenAlexHarvester)
    await ejecutar_cosecha(cosecha_id, TipoFuente.openalex, modo, parametros, session)
"""

from __future__ import annotations

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
    max_errores_consecutivos: int = 5,
) -> dict[str, Any]:
    """
    Orquesta una sesión de cosecha completa para el fuente_tipo dado.

    Flujo:
    1. Instancia el harvester y lo configura.
    2. Itera el generador async `cosechar()`.
    3. Persiste cada ResultadoCosecha en DB (upsert Paper + Persona + Coautoria).
    4. Ante error, llama a `manejar_error()` y actúa según la decisión.
    5. Devuelve un resumen al finalizar.
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
                await session.rollback()
                errores += 1
                log.warning(
                    "cosecha.integridad_saltada",
                    fuente_id=resultado.fuente_id,
                    error=str(exc.orig),
                )
            except Exception as exc:
                await session.rollback()
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

        contexto: dict[str, Any] = {
            "cosecha_id": cosecha_id,
            "fuente_tipo": fuente_tipo,
        }
        intento = errores_consecutivos
        decision = harvester.manejar_error(exc, contexto, intento)

        if decision.accion == AccionIntento.abortar:
            await _registrar_error_en_cosecha(session, cosecha_id, str(exc), NivelError.critical)
            log.error("cosecha.abortada", razon=decision.mensaje)
            raise

        if decision.accion == AccionIntento.reintentar:
            import asyncio

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
    """Persiste un resultado de cosecha: upsert Paper + Persona + Coautoria. Retorna True si fue nuevo."""
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

    paper_id = uuid.uuid4()
    paper_stmt = pg_insert(Paper).values(
        id=paper_id,
        openalex_id=openalex_id,
        doi=datos.get("doi"),
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
        paper_stmt = paper_stmt.on_conflict_do_update(
            index_elements=["openalex_id"],
            set_={
                "titulo": paper_stmt.excluded.titulo,
                "abstract_texto": paper_stmt.excluded.abstract_texto,
                "total_citas": paper_stmt.excluded.total_citas,
                "citas_por_año": paper_stmt.excluded.citas_por_año,
                "url_pdf": paper_stmt.excluded.url_pdf,
                "url_landing": paper_stmt.excluded.url_landing,
                "open_access": paper_stmt.excluded.open_access,
                "updated_at": func.now(),
            },
        ).returning(Paper.id, Paper.created_at, Paper.updated_at)
    else:
        paper_stmt = paper_stmt.on_conflict_do_nothing().returning(
            Paper.id, Paper.created_at, Paper.updated_at
        )

    paper_row = (await session.execute(paper_stmt)).first()
    if paper_row is None:
        return False

    paper_db_id: uuid.UUID = paper_row[0]
    is_nuevo: bool = paper_row[1] == paper_row[2]  # created_at == updated_at → nuevo

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
            raw_aff = "; ".join(str(x) for x in raw_aff_raw)[:500] or None
        else:
            raw_aff = str(raw_aff_raw or "")[:500] or None

        persona_values: dict[str, Any] = {
            "id": uuid.uuid4(),
            "nombre_completo": display_name,
            "nombre_normalizado": display_name.lower(),
            "tipo": TipoPersona.investigador.value,
            "fuente_principal": TipoFuente.openalex.value,
            "metadatos": {},
        }
        if author_oa_id:
            persona_values["openalex_id"] = author_oa_id
        if orcid:
            persona_values["orcid"] = orcid

        p_ins = pg_insert(Persona).values(**persona_values)
        if author_oa_id:
            persona_stmt = p_ins.on_conflict_do_update(
                index_elements=["openalex_id"],
                set_={"nombre_completo": p_ins.excluded.nombre_completo},
            ).returning(Persona.id)
        else:
            persona_stmt = p_ins.on_conflict_do_nothing().returning(Persona.id)

        persona_result = await session.execute(persona_stmt)
        persona_id_row = persona_result.scalar()
        if persona_id_row is None:
            continue

        coautoria_stmt = pg_insert(Coautoria).values(
            id=uuid.uuid4(),
            persona_id=persona_id_row,
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
        coautoria_stmt = coautoria_stmt.on_conflict_do_nothing()
        await session.execute(coautoria_stmt)

    return is_nuevo


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
