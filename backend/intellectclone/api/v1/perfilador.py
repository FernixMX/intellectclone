"""
Endpoints del perfilador de gemelos digitales.
TODO Fase D: implementar lógica real según docs/05_perfilador_y_gemelo.md §D5.

Endpoints:
  POST /perfilador/generar/{persona_id}        — disparar generación de gemelo
  GET  /perfilador/estado/{tarea_id}           — estado de la tarea Celery
  POST /perfilador/regenerar/{persona_id}      — forzar regeneración
  GET  /perfilador/candidatos-regeneracion     — lista de gemelos desactualizados
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/perfilador", tags=["perfilador"])


@router.post(  # type: ignore[misc]
    "/generar/{persona_id}",
    status_code=501,
    summary="[TODO Fase D] Disparar generación de gemelo digital",
)
async def generar_gemelo(persona_id: uuid.UUID) -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: generación de gemelos digitales (Fase D pendiente)",
    )


@router.get(  # type: ignore[misc]
    "/estado/{tarea_id}",
    status_code=501,
    summary="[TODO Fase D] Estado de tarea de generación de gemelo",
)
async def estado_tarea(tarea_id: str) -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: consulta de estado de tarea (Fase D pendiente)",
    )


@router.post(  # type: ignore[misc]
    "/regenerar/{persona_id}",
    status_code=501,
    summary="[TODO Fase D] Regenerar gemelo digital existente",
)
async def regenerar_gemelo(persona_id: uuid.UUID) -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: regeneración de gemelos (Fase D pendiente)",
    )


@router.get(  # type: ignore[misc]
    "/candidatos-regeneracion",
    status_code=501,
    summary="[TODO Fase D] Listar gemelos candidatos a regeneración",
)
async def candidatos_regeneracion() -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: alertas de regeneración (Fase D pendiente)",
    )
