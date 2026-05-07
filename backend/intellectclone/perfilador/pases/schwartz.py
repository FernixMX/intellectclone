"""
Pase Schwartz del perfilador.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §4 (Paso 3).

Responsabilidades:
- Inferir jerarquía de los 10 valores Schwartz (score 0-100 + rango)
- Identificar 3 valores dominantes y 2 subordinados
- Evidencia textual verbatim por cada valor
- score_veracidad_pase: auto-evaluación (0.0-1.0)
- Output persistido en gemelo.valores_schwartz (JSONB)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from intellectclone.llm.base import ClienteLLMBase


@dataclass
class ValorSchwartz:
    valor: str
    score: float
    evidencia: list[str]
    rango: int


@dataclass
class ResultadoSchwartz:
    valores: list[ValorSchwartz]
    valores_dominantes: list[str]
    valores_subordinados: list[str]
    score_veracidad_pase: float
    metadatos_llm: dict[str, Any] = field(default_factory=dict)


class PaseSchwartz:
    """TODO Fase D: ejecutar análisis axiológico Schwartz sobre el corpus."""

    async def ejecutar(
        self,
        corpus: str,
        metadatos: dict[str, Any],
        llm_client: ClienteLLMBase,
    ) -> ResultadoSchwartz:
        """TODO Fase D: invocar prompt Schwartz (prompts/schwartz_v01.md) via llm_client."""
        raise NotImplementedError("TODO Fase D: implementar PaseSchwartz.ejecutar")
