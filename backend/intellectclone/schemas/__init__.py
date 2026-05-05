"""
Schemas Pydantic de IntellectClone.
"""

from intellectclone.schemas.comun import PaginacionParams, RespuestaPaginada
from intellectclone.schemas.cuerpo_academico import CuerpoAcademicoCreate, CuerpoAcademicoRead
from intellectclone.schemas.dependencia import DependenciaCreate, DependenciaRead
from intellectclone.schemas.paper import PaperListItem, PaperRead
from intellectclone.schemas.persona import (
    PersonaCreate,
    PersonaListItem,
    PersonaRead,
    PersonaUpdate,
)

__all__ = [
    "PaginacionParams",
    "RespuestaPaginada",
    "CuerpoAcademicoCreate",
    "CuerpoAcademicoRead",
    "DependenciaCreate",
    "DependenciaRead",
    "PaperListItem",
    "PaperRead",
    "PersonaCreate",
    "PersonaListItem",
    "PersonaRead",
    "PersonaUpdate",
]
