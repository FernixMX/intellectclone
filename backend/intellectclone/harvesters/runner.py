"""
Runner de cosechadores: registro global y orquestación de una sesión de cosecha.

Uso:
    registrar_harvester(TipoFuente.openalex, OpenAlexHarvester)
    await ejecutar_cosecha(cosecha_id, TipoFuente.openalex, modo, parametros, session)
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.tipos import AccionIntento, NivelError

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_REGISTRY: dict[str, type[BaseHarvester]] = {}


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
    3. Ante error, llama a `manejar_error()` y actúa según la decisión.
    4. Registra cada fallo grave con `_registrar_error_en_cosecha()`.
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
            total += 1
            if resultado.es_nuevo:
                nuevos += 1
            if resultado.advertencias:
                log.warning(
                    "cosecha.advertencias_registro",
                    fuente_id=resultado.fuente_id,
                    advertencias=resultado.advertencias,
                )
            errores_consecutivos = 0

    except Exception as exc:
        errores += 1
        errores_consecutivos += 1

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
            log.info("cosecha.esperando_reintento", delay=decision.delay_segundos)
            await asyncio.sleep(decision.delay_segundos)

        if errores_consecutivos >= max_errores_consecutivos:
            await _registrar_error_en_cosecha(session, cosecha_id, str(exc), NivelError.critical)
            log.error("cosecha.abortada_por_errores", errores_consecutivos=errores_consecutivos)
            raise

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
    # Inserción real en log_cosecha se implementa en C4 cuando el modelo ORM esté listo.
    _ = session
