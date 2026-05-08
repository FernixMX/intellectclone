"""
Endpoints de la API v1 para Paper.
GET /api/v1/papers
GET /api/v1/papers/{id}
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.api.excepciones import EntidadNoEncontrada
from intellectclone.db import get_db
from intellectclone.models.enums import TipoPaper
from intellectclone.models.produccion import Coautoria, Paper
from intellectclone.schemas.comun import RespuestaPaginada
from intellectclone.schemas.paper import PaperListItem, PaperRead

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=RespuestaPaginada[PaperListItem])  # type: ignore[misc]
async def listar_papers(
    año: int | None = Query(default=None),
    tipo: TipoPaper | None = Query(default=None),
    q: str | None = Query(default=None, description="Búsqueda en título"),
    persona_id: uuid.UUID | None = Query(default=None, description="Filtrar por autor"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> RespuestaPaginada[PaperListItem]:
    """Lista papers con filtros básicos y paginación."""
    stmt = select(Paper)

    if persona_id is not None:
        stmt = stmt.join(Coautoria, Coautoria.paper_id == Paper.id).where(
            Coautoria.persona_id == persona_id
        )
    if año is not None:
        stmt = stmt.where(Paper.año == año)
    if tipo is not None:
        stmt = stmt.where(Paper.tipo == tipo)
    if q is not None:
        stmt = stmt.where(Paper.titulo.ilike(f"%{q}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(Paper.año.desc().nullslast(), Paper.titulo).limit(limit).offset(offset)
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    next_offset = offset + limit if offset + limit < total else None
    return RespuestaPaginada(
        total=total,
        limit=limit,
        offset=offset,
        items=[PaperListItem.model_validate(item) for item in items],
        next_offset=next_offset,
    )


@router.get("/{id}", response_model=PaperRead)  # type: ignore[misc]
async def obtener_paper(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> PaperRead:
    """Obtiene el detalle completo de un paper por su ID."""
    result = await session.get(Paper, id)
    if result is None:
        raise EntidadNoEncontrada("Paper", id)
    return PaperRead.model_validate(result)
