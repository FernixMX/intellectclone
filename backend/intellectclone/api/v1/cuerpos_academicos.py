"""
Endpoints de la API v1 para CuerpoAcademico.
GET /api/v1/cuerpos-academicos
GET /api/v1/cuerpos-academicos/{id}
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.api.excepciones import EntidadNoEncontrada
from intellectclone.db import get_db
from intellectclone.db.repositorios.cuerpo_academico import RepositorioCuerpoAcademico
from intellectclone.schemas.comun import RespuestaPaginada
from intellectclone.schemas.cuerpo_academico import CuerpoAcademicoRead

router = APIRouter(prefix="/cuerpos-academicos", tags=["cuerpos-academicos"])


@router.get("", response_model=RespuestaPaginada[CuerpoAcademicoRead])
async def listar_cuerpos_academicos(
    dependencia_id: uuid.UUID | None = Query(default=None),
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
) -> RespuestaPaginada[CuerpoAcademicoRead]:
    """Lista cuerpos académicos, opcionalmente filtrados por dependencia."""
    repo = RepositorioCuerpoAcademico(session)
    total, items = await repo.listar_por_dependencia(
        dependencia_id=dependencia_id, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return RespuestaPaginada(
        total=total,
        limit=limit,
        offset=offset,
        items=[CuerpoAcademicoRead.model_validate(item) for item in items],
        next_offset=next_offset,
    )


@router.get("/{id}", response_model=CuerpoAcademicoRead)
async def obtener_cuerpo_academico(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> CuerpoAcademicoRead:
    """Obtiene el detalle de un cuerpo académico por su ID."""
    repo = RepositorioCuerpoAcademico(session)
    instancia = await repo.obtener_por_id(id)
    if instancia is None:
        raise EntidadNoEncontrada("CuerpoAcademico", id)
    return CuerpoAcademicoRead.model_validate(instancia)
