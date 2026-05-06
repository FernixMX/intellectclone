"""
Endpoints de la API v1 para Dependencia.
GET /api/v1/dependencias
GET /api/v1/dependencias/{id}
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.api.excepciones import EntidadNoEncontrada
from intellectclone.db import get_db
from intellectclone.db.repositorios.dependencia import RepositorioDependencia
from intellectclone.schemas.comun import RespuestaPaginada
from intellectclone.schemas.dependencia import DependenciaRead

router = APIRouter(prefix="/dependencias", tags=["dependencias"])


@router.get("", response_model=RespuestaPaginada[DependenciaRead])  # type: ignore[misc]
async def listar_dependencias(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
) -> RespuestaPaginada[DependenciaRead]:
    """Lista todas las dependencias activas de la UAT."""
    repo = RepositorioDependencia(session)
    total, items = await repo.listar(limit=limit, offset=offset)
    next_offset = offset + limit if offset + limit < total else None
    return RespuestaPaginada(
        total=total,
        limit=limit,
        offset=offset,
        items=[DependenciaRead.model_validate(item) for item in items],
        next_offset=next_offset,
    )


@router.get("/{id}", response_model=DependenciaRead)  # type: ignore[misc]
async def obtener_dependencia(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> DependenciaRead:
    """Obtiene el detalle de una dependencia por su ID."""
    repo = RepositorioDependencia(session)
    instancia = await repo.obtener_por_id(id)
    if instancia is None:
        raise EntidadNoEncontrada("Dependencia", id)
    return DependenciaRead.model_validate(instancia)
