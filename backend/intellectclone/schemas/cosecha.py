"""
Schemas Pydantic para la API de cosechas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from intellectclone.models.enums import EstadoCosecha, TipoFuente


class CosechaRead(BaseModel):
    """Schema de lectura completa de una cosecha."""

    id: uuid.UUID
    fuente: TipoFuente
    estado: EstadoCosecha
    programada_para: datetime | None
    iniciada_at: datetime | None
    completada_at: datetime | None
    duracion_ms: int | None
    registros_procesados: int
    registros_nuevos: int
    registros_actualizados: int
    registros_descartados: int
    errores_count: int
    configuracion: dict[str, Any]
    log_resumen: str | None
    errores: list[Any] | None
    disparada_por: uuid.UUID | None
    disparada_manual: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CosechaDispararRequest(BaseModel):
    """Payload para disparar una cosecha."""

    fuente: TipoFuente
    modo: str = Field(default="completa", description="completa | incremental | persona_individual")
    parametros: dict[str, Any] = Field(default_factory=dict)
    configuracion: dict[str, Any] = Field(default_factory=dict)


class CosechaDispararResponse(BaseModel):
    """Respuesta inmediata al disparar una cosecha (HTTP 202)."""

    cosecha_id: uuid.UUID
    tarea_celery_id: str
    estimacion_duracion_minutos: int


class CosechaProgresoResponse(BaseModel):
    """Estado de progreso en tiempo real de una cosecha en curso."""

    estado: EstadoCosecha
    progreso_porcentaje: float | None
    registros_procesados: int
    registros_estimados_totales: int | None
    velocidad_rps: float | None
    eta_segundos: int | None
    errores_count: int
    ultimo_error: str | None


class EstadoFuenteResponse(BaseModel):
    """Estado consolidado de la última cosecha por fuente."""

    fuente: TipoFuente
    ultima_cosecha_id: uuid.UUID | None
    ultimo_estado: EstadoCosecha | None
    ultima_completada_at: datetime | None
    registros_procesados: int
    errores_count: int
