"""
Calculador de los tres scores de calidad del gemelo.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §8 (Paso 7).

Scores:
- score_veracidad: promedio ponderado de scores por pase
    (HEXACO 0.30 + Schwartz 0.25 + Idiolecto 0.20 + Posturas 0.25)
- score_completitud: función de n_papers, años_cubiertos, diversidad_fuentes
- score_consistencia: validación cruzada via LLM (Gemini Flash por default)
    ¿HEXACO consistente con Schwartz? ¿Posturas consistentes con Schwartz?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoresCalidad:
    score_veracidad: float
    score_completitud: float
    score_consistencia: float
    detalle: dict[str, Any]


class CalculadorScores:
    """TODO Fase D: calcular los tres scores de calidad del gemelo."""

    def calcular_veracidad(
        self,
        score_hexaco: float,
        score_schwartz: float,
        score_idiolecto: float,
        score_posturas: float,
    ) -> float:
        """TODO Fase D: promedio ponderado (0.30/0.25/0.20/0.25)."""
        raise NotImplementedError("TODO Fase D: implementar calcular_veracidad")

    def calcular_completitud(
        self,
        n_papers: int,
        años_cubiertos: list[int],
        n_fuentes: int,
    ) -> float:
        """TODO Fase D: función logarítmica sobre n_papers + bonus por diversidad."""
        raise NotImplementedError("TODO Fase D: implementar calcular_completitud")

    async def calcular_consistencia(
        self,
        hexaco: dict[str, Any],
        schwartz: dict[str, Any],
        posturas: dict[str, Any],
        llm_client: Any,
    ) -> float:
        """TODO Fase D: validación cruzada via LLM (prompts/validacion_consistencia_v01.md)."""
        raise NotImplementedError("TODO Fase D: implementar calcular_consistencia")
