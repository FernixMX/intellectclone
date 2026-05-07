"""
Sintetizador del system_prompt operativo del gemelo digital.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §7 (Paso 6).

Responsabilidades:
- Construir system_prompt por template Jinja2 (determinístico, no probabilístico)
- Combinar outputs de los 4 pases + metadatos de la persona
- Paso opcional de afinación por LLM (desactivable por admin)
- Garantizar reproducibilidad: mismo JSON de gemelo → mismo system_prompt
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ResultadoSintesis:
    system_prompt: str
    version_template: str
    afinado_por_llm: bool
    metadatos: dict[str, Any]


class Sintetizador:
    """TODO Fase D: construir system_prompt operativo del gemelo via template Jinja2."""

    def sintetizar(
        self,
        hexaco: dict[str, Any],
        schwartz: dict[str, Any],
        idiolecto: dict[str, Any],
        posturas: dict[str, Any],
        metadatos_persona: dict[str, Any],
    ) -> ResultadoSintesis:
        """TODO Fase D: renderizar template Jinja2 con los outputs de los pases."""
        raise NotImplementedError("TODO Fase D: implementar Sintetizador.sintetizar")
