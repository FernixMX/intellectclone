"""
Schemas Pydantic para Paper.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from intellectclone.models.enums import TipoFuente, TipoPaper


class PaperRead(BaseModel):
    """Schema de lectura completa de un paper (sin embedding)."""

    id: uuid.UUID
    doi: str | None
    openalex_id: str | None
    handle_riuat: str | None
    tipo: TipoPaper
    titulo: str
    titulo_normalizado: str | None
    abstract_texto: str | None
    año: int | None
    fecha_publicacion: date | None
    idioma: str | None
    revista: str | None
    issn: str | None
    editorial: str | None
    volumen: str | None
    numero: str | None
    paginas: str | None
    open_access: bool | None
    url_pdf: str | None
    url_landing: str | None
    license: str | None
    total_citas: int
    citas_por_año: dict | None  # type: ignore[type-arg]
    conceptos: list[str] | None
    fuente_origen: TipoFuente | None
    cosecha_id: uuid.UUID | None
    metadatos: dict  # type: ignore[type-arg]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperListItem(BaseModel):
    """Versión compacta de Paper para listados."""

    id: uuid.UUID
    doi: str | None
    tipo: TipoPaper
    titulo: str
    año: int | None
    revista: str | None
    total_citas: int
    fuente_origen: TipoFuente | None

    model_config = {"from_attributes": True}
