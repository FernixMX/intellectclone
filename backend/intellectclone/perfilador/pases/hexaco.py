"""
Pase HEXACO del perfilador.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §3 (Paso 2).

Responsabilidades:
- Ejecutar prompt HEXACO contra LLM configurado (default: claude-sonnet-4-6)
- Inferir 6 dimensiones: extraversion, neuroticismo, responsabilidad, amabilidad,
  apertura, honestidad_humildad
- Cada dimensión: nivel (muy_bajo..muy_alto), evidencia textual, justificacion en español
- score_veracidad_pase: auto-evaluación de confianza del LLM (0.0-1.0)
- Retry JSON malformado via ClienteLLMBase.completar_json (máx 2 reintentos)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.models.enums import NivelRasgo


@dataclass
class RasgoHexaco:
    nivel: NivelRasgo
    evidencia: list[str]
    justificacion: str


@dataclass
class ResultadoHexaco:
    extraversion: RasgoHexaco
    neuroticismo: RasgoHexaco
    responsabilidad: RasgoHexaco
    amabilidad: RasgoHexaco
    apertura: RasgoHexaco
    honestidad_humildad: RasgoHexaco
    score_veracidad_pase: float
    metadatos_llm: dict[str, Any] = field(default_factory=dict)


class PaseHexaco:
    """TODO Fase D: ejecutar análisis psicométrico HEXACO sobre el corpus."""

    async def ejecutar(
        self,
        corpus: str,
        metadatos: dict[str, Any],
        llm_client: ClienteLLMBase,
    ) -> ResultadoHexaco:
        """TODO Fase D: invocar prompt HEXACO (prompts/hexaco_v01.md) via llm_client."""
        raise NotImplementedError("TODO Fase D: implementar PaseHexaco.ejecutar")
