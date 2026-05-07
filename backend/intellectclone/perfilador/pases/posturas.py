"""
Pase de posturas temáticas del perfilador.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §6 (Paso 5).

Responsabilidades:
- Parte A — Tronco común UAT: evaluar postura sobre 18 temas institucionales
  (leídos de tabla tema_tronco_comun en DB); si no hay evidencia → "sin_evidencia"
- Parte B — Posturas dinámicas: identificar 5-10 temas específicos del corpus
  con postura clara
- score_veracidad_pase
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.models.enums import IntensidadRespuesta, PosturaRespuesta


@dataclass
class PosturaTema:
    tema: str
    postura: PosturaRespuesta
    intensidad: IntensidadRespuesta | None
    evidencia: list[str]
    confianza: float


@dataclass
class ResultadoPosturas:
    tronco_comun: list[PosturaTema]
    posturas_dinamicas: list[PosturaTema]
    score_veracidad_pase: float
    metadatos_llm: dict[str, Any] = field(default_factory=dict)


class PasePosturas:
    """TODO Fase D: ejecutar inferencia de posturas temáticas sobre el corpus."""

    async def ejecutar(
        self,
        corpus: str,
        metadatos: dict[str, Any],
        temas_tronco: list[dict[str, Any]],
        llm_client: ClienteLLMBase,
    ) -> ResultadoPosturas:
        """TODO Fase D: invocar prompt posturas (prompts/posturas_v01.md) vía llm_client."""
        raise NotImplementedError("TODO Fase D: implementar PasePosturas.ejecutar")
