"""
Schemas Pydantic reutilizables para paginación y respuestas comunes.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginacionParams(BaseModel):
    """Parámetros de paginación para endpoints de listado."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: str = Field(default="created_at")


class RespuestaPaginada(BaseModel, Generic[T]):
    """Respuesta paginada genérica para listados."""

    total: int
    limit: int
    offset: int
    items: list[T]
    next_offset: int | None

    model_config = {"arbitrary_types_allowed": True}
