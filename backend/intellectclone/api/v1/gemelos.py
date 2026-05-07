"""
Endpoints de gemelos digitales.
TODO Fase D: implementar lógica real según docs/05_perfilador_y_gemelo.md §D5.

Endpoints:
  GET /gemelos/{persona_id}          — gemelo actual de una persona
  GET /gemelos/{persona_id}/versiones — historial de versiones del gemelo
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/gemelos", tags=["gemelos"])


@router.get(  # type: ignore[misc]
    "/{persona_id}",
    status_code=501,
    summary="[TODO Fase D] Obtener gemelo digital actual de una persona",
)
async def obtener_gemelo(persona_id: uuid.UUID) -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: consulta de gemelo digital (Fase D pendiente)",
    )


@router.get(  # type: ignore[misc]
    "/{persona_id}/versiones",
    status_code=501,
    summary="[TODO Fase D] Historial de versiones del gemelo de una persona",
)
async def versiones_gemelo(persona_id: uuid.UUID) -> None:
    raise HTTPException(
        status_code=501,
        detail="No implementado: historial de versiones (Fase D pendiente)",
    )
