"""
Schemas Pydantic para los endpoints de analítica bibliométrica.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class PuntoPapersPorAnio(BaseModel):
    año: int
    total_papers: int
    total_papers_uat: int = 0
    total_citas: int


class SerieTemporalPapersResponse(BaseModel):
    datos: list[PuntoPapersPorAnio]
    total_papers_historico: int


class TopDependenciaItem(BaseModel):
    dependencia_id: uuid.UUID
    nombre: str
    nombre_corto: str | None
    total_papers: int
    total_personas: int


class TopDependenciasResponse(BaseModel):
    items: list[TopDependenciaItem]


class TopInvestigadorItem(BaseModel):
    persona_id: uuid.UUID
    nombre_completo: str
    nivel_snii: str | None
    n_papers_cosechados: int
    total_citas: int
    indice_h: int


class TopInvestigadoresResponse(BaseModel):
    items: list[TopInvestigadorItem]


class NodoCoautoria(BaseModel):
    persona_id: uuid.UUID
    nombre_completo: str
    dependencia_id: uuid.UUID | None
    grado: int
    es_externo: bool = False


class AristaCoautoria(BaseModel):
    persona_a_id: uuid.UUID
    persona_b_id: uuid.UUID
    n_papers_comunes: int


class RedCoautoriaResponse(BaseModel):
    nodos: list[NodoCoautoria]
    aristas: list[AristaCoautoria]
    total_nodos: int
    total_aristas: int


class EstadisticasGlobalesResponse(BaseModel):
    total_personas: int
    total_papers: int
    total_papers_uat: int
    total_coautorias: int
    total_dependencias: int
    total_cuerpos_academicos: int
