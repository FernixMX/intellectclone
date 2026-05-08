"""
Endpoints de la API v1 para Persona.
GET  /api/v1/personas
GET  /api/v1/personas/{id}
POST /api/v1/personas
PATCH /api/v1/personas/{id}
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.api.excepciones import EntidadNoEncontrada
from intellectclone.db import get_db
from intellectclone.db.repositorios.persona import RepositorioPersona
from intellectclone.models.enums import NivelSnii, TipoPersona
from intellectclone.schemas.comun import RespuestaPaginada
from intellectclone.schemas.persona import (
    PersonaCreate,
    PersonaListItem,
    PersonaRead,
    PersonaUpdate,
)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=RespuestaPaginada[PersonaListItem])  # type: ignore[misc]
async def listar_personas(
    tipo: TipoPersona | None = Query(default=None),
    dependencia_id: uuid.UUID | None = Query(default=None),
    cuerpo_academico_id: uuid.UUID | None = Query(default=None),
    nivel_snii: NivelSnii | None = Query(default=None),
    tiene_gemelo_validado: bool | None = Query(default=None),
    solo_uat: bool | None = Query(default=None, description="Solo personas con dependencia UAT"),
    q: str | None = Query(default=None, description="Búsqueda por nombre"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> RespuestaPaginada[PersonaListItem]:
    """Lista personas con filtros opcionales y paginación."""
    repo = RepositorioPersona(session)
    total, items = await repo.listar_con_filtros(
        tipo=tipo,
        dependencia_id=dependencia_id,
        cuerpo_academico_id=cuerpo_academico_id,
        nivel_snii=nivel_snii,
        tiene_gemelo_validado=tiene_gemelo_validado,
        solo_uat=solo_uat,
        q=q,
        limit=limit,
        offset=offset,
    )
    next_offset = offset + limit if offset + limit < total else None
    return RespuestaPaginada(
        total=total,
        limit=limit,
        offset=offset,
        items=[PersonaListItem.model_validate(item) for item in items],
        next_offset=next_offset,
    )


@router.get("/{id}", response_model=PersonaRead)  # type: ignore[misc]
async def obtener_persona(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> PersonaRead:
    """Obtiene el detalle completo de una persona por su ID."""
    repo = RepositorioPersona(session)
    instancia = await repo.obtener_con_relaciones(id)
    if instancia is None:
        raise EntidadNoEncontrada("Persona", id)
    return PersonaRead.model_validate(instancia)


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)  # type: ignore[misc]
async def crear_persona(
    datos: PersonaCreate,
    session: AsyncSession = Depends(get_db),
) -> PersonaRead:
    """
    Crea una persona manualmente.
    Por ahora no requiere autenticación — se agrega en Fase D.
    """
    repo = RepositorioPersona(session)
    nueva_persona = await repo.crear(datos.model_dump())
    return PersonaRead.model_validate(nueva_persona)


@router.patch("/{id}", response_model=PersonaRead)  # type: ignore[misc]
async def actualizar_persona(
    id: uuid.UUID,
    datos: PersonaUpdate,
    session: AsyncSession = Depends(get_db),
) -> PersonaRead:
    """Actualiza parcialmente los datos de una persona."""
    repo = RepositorioPersona(session)
    instancia = await repo.obtener_por_id(id)
    if instancia is None:
        raise EntidadNoEncontrada("Persona", id)
    # Solo enviamos campos que no son None
    campos_a_actualizar = {k: v for k, v in datos.model_dump().items() if v is not None}
    actualizada = await repo.actualizar(instancia, campos_a_actualizar)
    return PersonaRead.model_validate(actualizada)
