"""
Pase idiolecto del perfilador.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §5 (Paso 4).

Responsabilidades:
- Cálculos cuantitativos en Python (no LLM) con spaCy es_core_news_md:
    longitud_promedio_frase, riqueza_lexica (TTR sobre lemas), n-grams top
- Cálculos cualitativos via LLM (default: gemini-2.5-flash):
    firma_linguistica, modus_operandi, tono_dominante, registro
- score_veracidad_pase
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from intellectclone.llm.base import ClienteLLMBase


@dataclass
class ResultadoIdiolecto:
    longitud_promedio_frase: float
    riqueza_lexica: float
    ngrams_top_unigram: list[str]
    ngrams_top_bigram: list[str]
    ngrams_top_trigram: list[str]
    firma_linguistica: str
    modus_operandi: str
    tono_dominante: str
    registro: str
    score_veracidad_pase: float
    metadatos_llm: dict[str, Any] = field(default_factory=dict)


class PaseIdiolecto:
    """TODO Fase D: ejecutar análisis lingüístico (idiolecto) sobre el corpus."""

    async def ejecutar(
        self,
        corpus: str,
        metadatos: dict[str, Any],
        llm_client: ClienteLLMBase,
    ) -> ResultadoIdiolecto:
        """
        TODO Fase D:
        1. calcular_metricas_idiolecto(corpus) con spaCy — sin LLM
        2. invocar prompt idiolecto (prompts/idiolecto_cualitativo_v01.md) vía llm_client
        """
        raise NotImplementedError("TODO Fase D: implementar PaseIdiolecto.ejecutar")
