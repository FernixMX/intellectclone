"""
Schemas Pydantic para Persona.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from intellectclone.models.enums import NivelSnii, TipoFuente, TipoPersona


class PersonaRead(BaseModel):
    """Schema de lectura completa de una persona (sin embedding, sin password)."""

    id: uuid.UUID
    nombre_completo: str
    nombre_normalizado: str
    primer_nombre: str | None
    apellido_paterno: str | None
    apellido_materno: str | None
    tipo: TipoPersona
    orcid: str | None
    openalex_id: str | None
    scopus_id: str | None
    cvu_conacyt: str | None
    google_scholar_id: str | None
    dependencia_id: uuid.UUID | None
    dependencia_nombre: str | None = None
    cuerpo_academico_id: uuid.UUID | None
    cargo: str | None
    nivel_snii: NivelSnii | None
    snii_vigente_hasta: date | None
    grado_maximo: str | None
    grado_disciplina: str | None
    total_publicaciones: int
    total_citas: int
    indice_h: int
    indice_i10: int
    primera_publicacion: date | None
    ultima_publicacion: date | None
    email_publico: str | None
    sitio_web: str | None
    activa: bool
    motivo_baja: str | None
    fecha_baja: datetime | None
    fuente_principal: TipoFuente | None
    metadatos: dict  # type: ignore[type-arg]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonaCreate(BaseModel):
    """Schema para crear una persona manualmente (solo admin)."""

    nombre_completo: str = Field(..., max_length=255)
    nombre_normalizado: str = Field(..., max_length=255)
    primer_nombre: str | None = Field(default=None, max_length=100)
    apellido_paterno: str | None = Field(default=None, max_length=100)
    apellido_materno: str | None = Field(default=None, max_length=100)
    tipo: TipoPersona = TipoPersona.investigador
    orcid: str | None = Field(default=None, max_length=19)
    openalex_id: str | None = Field(default=None, max_length=50)
    scopus_id: str | None = Field(default=None, max_length=50)
    cvu_conacyt: str | None = Field(default=None, max_length=20)
    google_scholar_id: str | None = Field(default=None, max_length=50)
    dependencia_id: uuid.UUID | None = None
    cuerpo_academico_id: uuid.UUID | None = None
    cargo: str | None = Field(default=None, max_length=255)
    nivel_snii: NivelSnii | None = None
    snii_vigente_hasta: date | None = None
    grado_maximo: str | None = Field(default=None, max_length=100)
    grado_disciplina: str | None = Field(default=None, max_length=255)
    email_publico: str | None = Field(default=None, max_length=255)
    sitio_web: str | None = Field(default=None, max_length=500)
    fuente_principal: TipoFuente | None = None
    metadatos: dict = Field(default_factory=dict)  # type: ignore[type-arg]


class PersonaUpdate(BaseModel):
    """Schema para actualización parcial de una persona (PATCH)."""

    nombre_completo: str | None = Field(default=None, max_length=255)
    nombre_normalizado: str | None = Field(default=None, max_length=255)
    primer_nombre: str | None = Field(default=None, max_length=100)
    apellido_paterno: str | None = Field(default=None, max_length=100)
    apellido_materno: str | None = Field(default=None, max_length=100)
    tipo: TipoPersona | None = None
    orcid: str | None = Field(default=None, max_length=19)
    openalex_id: str | None = Field(default=None, max_length=50)
    scopus_id: str | None = Field(default=None, max_length=50)
    cvu_conacyt: str | None = Field(default=None, max_length=20)
    google_scholar_id: str | None = Field(default=None, max_length=50)
    dependencia_id: uuid.UUID | None = None
    cuerpo_academico_id: uuid.UUID | None = None
    cargo: str | None = Field(default=None, max_length=255)
    nivel_snii: NivelSnii | None = None
    snii_vigente_hasta: date | None = None
    grado_maximo: str | None = Field(default=None, max_length=100)
    grado_disciplina: str | None = Field(default=None, max_length=255)
    email_publico: str | None = Field(default=None, max_length=255)
    sitio_web: str | None = Field(default=None, max_length=500)
    activa: bool | None = None
    motivo_baja: str | None = None
    fuente_principal: TipoFuente | None = None
    metadatos: dict | None = None  # type: ignore[type-arg]


class PersonaListItem(BaseModel):
    """Versión compacta de Persona para listados."""

    id: uuid.UUID
    nombre_completo: str
    tipo: TipoPersona
    nivel_snii: NivelSnii | None
    dependencia_id: uuid.UUID | None
    cargo: str | None
    total_publicaciones: int
    indice_h: int
    activa: bool

    model_config = {"from_attributes": True}
