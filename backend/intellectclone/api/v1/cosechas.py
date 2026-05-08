"""
Endpoints de la API v1 para gestión de cosechas.
GET  /api/v1/cosechas
GET  /api/v1/cosechas/estado-fuentes
GET  /api/v1/cosechas/{id}
GET  /api/v1/cosechas/{id}/progreso
POST /api/v1/cosechas/disparar
POST /api/v1/cosechas/snii-api
POST /api/v1/cosechas/{id}/cancelar
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.api.excepciones import EntidadNoEncontrada, EstadoInvalido
from intellectclone.db import get_db
from intellectclone.db.repositorios.cosecha import RepositorioCosecha
from intellectclone.harvesters.snii_api import ejecutar_cosecha_snii_api
from intellectclone.models.enums import EstadoCosecha, TipoFuente
from intellectclone.schemas.comun import RespuestaPaginada
from intellectclone.schemas.cosecha import (
    CosechaDispararRequest,
    CosechaDispararResponse,
    CosechaProgresoResponse,
    CosechaRead,
    EstadoFuenteResponse,
    SniiApiResultadoResponse,
)
from intellectclone.tasks.cosecha import cosechar_fuente

router = APIRouter(prefix="/cosechas", tags=["cosechas"])

_ESTIMACION_MINUTOS: dict[str, int] = {
    "completa": 30,
    "incremental": 5,
    "persona_individual": 2,
}


@router.get("", response_model=RespuestaPaginada[CosechaRead])  # type: ignore[misc]
async def listar_cosechas(
    fuente: TipoFuente | None = Query(default=None),
    estado: EstadoCosecha | None = Query(default=None),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> RespuestaPaginada[CosechaRead]:
    """Lista cosechas con filtros opcionales."""
    repo = RepositorioCosecha(session)
    total, items = await repo.listar_con_filtros(
        fuente=fuente,
        estado=estado,
        desde=desde,
        hasta=hasta,
        limit=limit,
        offset=offset,
    )
    next_offset = offset + limit if offset + limit < total else None
    return RespuestaPaginada(
        total=total,
        limit=limit,
        offset=offset,
        items=[CosechaRead.model_validate(item) for item in items],
        next_offset=next_offset,
    )


@router.get("/estado-fuentes", response_model=list[EstadoFuenteResponse])  # type: ignore[misc]
async def estado_fuentes(
    session: AsyncSession = Depends(get_db),
) -> list[EstadoFuenteResponse]:
    """Devuelve el estado de la última cosecha por cada fuente registrada."""
    repo = RepositorioCosecha(session)
    resultado: list[EstadoFuenteResponse] = []
    for fuente in TipoFuente:
        ultima = await repo.obtener_ultima_por_fuente(fuente)
        if ultima is not None:
            resultado.append(
                EstadoFuenteResponse(
                    fuente=fuente,
                    ultima_cosecha_id=ultima.id,
                    ultimo_estado=ultima.estado,
                    ultima_completada_at=ultima.completada_at,
                    registros_procesados=ultima.registros_procesados,
                    errores_count=ultima.errores_count,
                )
            )
        else:
            resultado.append(
                EstadoFuenteResponse(
                    fuente=fuente,
                    ultima_cosecha_id=None,
                    ultimo_estado=None,
                    ultima_completada_at=None,
                    registros_procesados=0,
                    errores_count=0,
                )
            )
    return resultado


@router.post("/disparar", status_code=202, response_model=CosechaDispararResponse)  # type: ignore[misc]
async def disparar_cosecha(
    body: CosechaDispararRequest,
    session: AsyncSession = Depends(get_db),
) -> CosechaDispararResponse:
    """
    Dispara una cosecha manual. Crea el registro en DB y encola la tarea Celery.
    Devuelve 202 con el ID de cosecha y el ID de tarea Celery.
    """
    repo = RepositorioCosecha(session)
    cosecha = await repo.crear_cosecha(
        fuente=body.fuente,
        modo=body.modo,
        parametros=body.parametros,
        configuracion=body.configuracion,
        disparada_por=None,
    )
    await session.commit()

    tarea = cosechar_fuente.delay(
        cosecha_id=str(cosecha.id),
        fuente_tipo=body.fuente.value,
        modo=body.modo,
        parametros=body.parametros,
        config=body.configuracion,
    )

    estimacion = _ESTIMACION_MINUTOS.get(body.modo, 15)
    return CosechaDispararResponse(
        cosecha_id=cosecha.id,
        tarea_celery_id=tarea.id,
        estimacion_duracion_minutos=estimacion,
    )


@router.post(  # type: ignore[misc]
    "/snii-api",
    response_model=SniiApiResultadoResponse,
    summary="Cosecha SNII vía API JSON pública de produccioncientifica.uat.edu.mx",
)
async def disparar_cosecha_snii_api(
    session: AsyncSession = Depends(get_db),
) -> SniiApiResultadoResponse:
    """
    Cosecha sincrónica de investigadores SNII y dependencias de la UAT.
    Actualiza nivel_snii y dependencia_id en personas ya existentes.
    """
    resultado = await ejecutar_cosecha_snii_api(session)
    return SniiApiResultadoResponse(**resultado)


@router.get("/{id}", response_model=CosechaRead)  # type: ignore[misc]
async def obtener_cosecha(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> CosechaRead:
    """Obtiene el detalle de una cosecha por su ID."""
    from intellectclone.models.sistema import Cosecha as CosechaModel

    cosecha = await session.get(CosechaModel, id)
    if cosecha is None:
        raise EntidadNoEncontrada("Cosecha", id)
    return CosechaRead.model_validate(cosecha)


@router.get("/{id}/progreso", response_model=CosechaProgresoResponse)  # type: ignore[misc]
async def progreso_cosecha(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> CosechaProgresoResponse:
    """Devuelve el estado de progreso de una cosecha."""
    from intellectclone.models.sistema import Cosecha as CosechaModel

    cosecha = await session.get(CosechaModel, id)
    if cosecha is None:
        raise EntidadNoEncontrada("Cosecha", id)

    velocidad: float | None = None
    eta: int | None = None
    if cosecha.iniciada_at is not None and cosecha.registros_procesados > 0:
        from datetime import UTC

        elapsed = (datetime.now(UTC) - cosecha.iniciada_at).total_seconds()
        if elapsed > 0:
            velocidad = cosecha.registros_procesados / elapsed

    return CosechaProgresoResponse(
        estado=cosecha.estado,
        progreso_porcentaje=None,
        registros_procesados=cosecha.registros_procesados,
        registros_estimados_totales=None,
        velocidad_rps=velocidad,
        eta_segundos=eta,
        errores_count=cosecha.errores_count,
        ultimo_error=cosecha.log_resumen,
    )


@router.post("/{id}/cancelar", response_model=CosechaRead)  # type: ignore[misc]
async def cancelar_cosecha(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> CosechaRead:
    """Cancela una cosecha programada o en curso."""
    from intellectclone.models.sistema import Cosecha as CosechaModel

    cosecha = await session.get(CosechaModel, id)
    if cosecha is None:
        raise EntidadNoEncontrada("Cosecha", id)

    estados_cancelables = {EstadoCosecha.programada, EstadoCosecha.en_curso}
    if cosecha.estado not in estados_cancelables:
        raise EstadoInvalido("Cosecha", cosecha.estado.value, "cancelar")

    cosecha.estado = EstadoCosecha.cancelada
    await session.commit()
    await session.refresh(cosecha)
    return CosechaRead.model_validate(cosecha)
