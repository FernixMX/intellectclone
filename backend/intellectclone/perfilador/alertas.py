"""
Sistema de alertas de gemelos desactualizados.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §9.

Un gemelo se marca como candidato a regeneración cuando:
- Tiene 5+ papers nuevos cosechados después de la fecha de generación, O
- Pasaron 6 meses desde la última generación y hay al menos 1 paper nuevo, O
- El prompt del perfilador se actualizó (prompt_perfilador_version cambió), O
- El admin marcó manualmente al gemelo como obsoleto.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class CandidatoRegeneracion:
    persona_id: uuid.UUID
    gemelo_id: uuid.UUID
    razon: str
    papers_nuevos: int
    meses_desde_generacion: float
    urgencia: float


class SistemaAlertas:
    """TODO Fase D: evaluar qué gemelos deben ser regenerados."""

    async def obtener_candidatos(
        self,
        session: Any,
    ) -> list[CandidatoRegeneracion]:
        """TODO Fase D: query DB para detectar gemelos desactualizados."""
        raise NotImplementedError("TODO Fase D: implementar SistemaAlertas.obtener_candidatos")
