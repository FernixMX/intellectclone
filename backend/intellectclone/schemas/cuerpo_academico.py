"""
Schemas Pydantic para CuerpoAcademico.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CuerpoAcademicoRead(BaseModel):
    """Schema de lectura completa de un cuerpo académico."""

    id: uuid.UUID
    codigo: str | None
    nombre: str
    estatus: str | None
    dependencia_id: uuid.UUID | None
    lineas_generacion: list[str] | None
    fecha_registro: date | None
    activo: bool
    metadatos: dict  # type: ignore[type-arg]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CuerpoAcademicoCreate(BaseModel):
    """Schema para crear un cuerpo académico manualmente."""

    codigo: str | None = Field(default=None, max_length=50)
    nombre: str = Field(..., max_length=500)
    estatus: str | None = Field(default=None, max_length=50)
    dependencia_id: uuid.UUID | None = None
    lineas_generacion: list[str] | None = None
    fecha_registro: date | None = None
    activo: bool = True
    metadatos: dict = Field(default_factory=dict)  # type: ignore[type-arg]
