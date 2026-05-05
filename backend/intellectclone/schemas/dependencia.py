"""
Schemas Pydantic para Dependencia.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DependenciaRead(BaseModel):
    """Schema de lectura completa de una dependencia."""

    id: uuid.UUID
    codigo: str
    nombre: str
    nombre_corto: str | None
    tipo: str
    campus: str | None
    sitio_web: str | None
    descripcion: str | None
    activa: bool
    metadatos: dict  # type: ignore[type-arg]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DependenciaCreate(BaseModel):
    """Schema para crear una dependencia manualmente."""

    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=255)
    nombre_corto: str | None = Field(default=None, max_length=100)
    tipo: str = Field(..., max_length=50)
    campus: str | None = Field(default=None, max_length=100)
    sitio_web: str | None = Field(default=None, max_length=500)
    descripcion: str | None = None
    activa: bool = True
    metadatos: dict = Field(default_factory=dict)  # type: ignore[type-arg]
