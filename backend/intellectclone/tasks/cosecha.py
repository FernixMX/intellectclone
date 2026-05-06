"""
Tarea Celery para ejecutar una cosecha de harvester.
Corre en worker separado; usa asyncio.run() para ejecutar el código async del harvester.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from intellectclone.celery_app import celery_app
from intellectclone.db.session import _get_session_factory
from intellectclone.harvesters.runner import ejecutar_cosecha
from intellectclone.models.enums import EstadoCosecha
from intellectclone.models.sistema import Cosecha

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    bind=True,
    name="intellectclone.tasks.cosecha.cosechar_fuente",
    max_retries=0,
)
def cosechar_fuente(
    self: Any,
    cosecha_id: str,
    fuente_tipo: str,
    modo: str,
    parametros: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Tarea Celery sincrónica que envuelve el flujo async de cosecha.
    Actualiza el registro Cosecha en DB antes y después de ejecutar.
    """
    return asyncio.run(
        _ejecutar_cosecha_async(self.request.id, cosecha_id, fuente_tipo, modo, parametros, config)
    )


async def _ejecutar_cosecha_async(
    tarea_id: str | None,
    cosecha_id: str,
    fuente_tipo: str,
    modo: str,
    parametros: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    log = logger.bind(cosecha_id=cosecha_id, fuente_tipo=fuente_tipo, tarea_id=tarea_id)
    factory = _get_session_factory()

    inicio = datetime.now(UTC)

    async with factory() as session:
        cosecha = await session.get(Cosecha, uuid.UUID(cosecha_id))
        if cosecha is None:
            raise ValueError(f"Cosecha {cosecha_id} no encontrada en DB")

        cosecha.estado = EstadoCosecha.en_curso
        cosecha.iniciada_at = inicio
        await session.commit()
        log.info("cosecha.task.iniciada")

    try:
        async with factory() as session:
            resumen = await ejecutar_cosecha(
                cosecha_id=cosecha_id,
                fuente_tipo=fuente_tipo,
                modo=modo,
                parametros=parametros,
                config=config,
                session=session,
            )

        fin = datetime.now(UTC)
        duracion_ms = int((fin - inicio).total_seconds() * 1000)

        async with factory() as session:
            cosecha = await session.get(Cosecha, uuid.UUID(cosecha_id))
            if cosecha is not None:
                tiene_errores = resumen.get("errores", 0) > 0
                cosecha.estado = (
                    EstadoCosecha.completada_con_errores
                    if tiene_errores
                    else EstadoCosecha.completada
                )
                cosecha.completada_at = fin
                cosecha.duracion_ms = duracion_ms
                cosecha.registros_procesados = resumen.get("total", 0)
                cosecha.registros_nuevos = resumen.get("nuevos", 0)
                cosecha.errores_count = resumen.get("errores", 0)
                await session.commit()

        log.info("cosecha.task.completada", duracion_ms=duracion_ms, **resumen)
        return resumen

    except Exception as exc:
        fin = datetime.now(UTC)
        duracion_ms = int((fin - inicio).total_seconds() * 1000)

        async with factory() as session:
            cosecha = await session.get(Cosecha, uuid.UUID(cosecha_id))
            if cosecha is not None:
                cosecha.estado = EstadoCosecha.fallida
                cosecha.completada_at = fin
                cosecha.duracion_ms = duracion_ms
                cosecha.log_resumen = str(exc)
                await session.commit()

        log.error("cosecha.task.fallida", error=str(exc))
        raise
