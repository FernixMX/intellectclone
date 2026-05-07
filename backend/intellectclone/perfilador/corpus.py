"""
Preparador de corpus textual para el perfilador.
TODO Fase D: implementar según docs/05_perfilador_y_gemelo.md §Paso 1.

Lógica pendiente:
- Consulta coautoria → paper.abstract_texto con pesos (primer autor 1.0,
  correspondiente 0.9, coautor 0.7)
- Consulta documento_corpus estado=procesado peso 0.8
- Selección estratificada si supera 80k chars (recientes 30k + citados 30k + aleatorio 15k)
- Falla explícita si < 3k chars: lanza CorpusSuficienteError con estado sin_corpus
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntradaCorpus:
    """Una pieza de texto con su fuente y peso de relevancia."""

    texto: str
    peso: float
    fuente: str
    año: int | None = None
    total_citas: int = 0
    metadatos: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusPreparado:
    """Corpus consolidado listo para pasar al perfilador."""

    persona_id: uuid.UUID
    texto_consolidado: str
    entradas: list[EntradaCorpus]
    total_caracteres: int
    n_papers: int
    n_documentos: int
    años_cubiertos: list[int]
    metadatos: dict[str, Any] = field(default_factory=dict)


class CorpusSuficienteError(Exception):
    """Corpus insuficiente para perfilar (< 3 000 caracteres)."""

    def __init__(self, persona_id: uuid.UUID, total_caracteres: int) -> None:
        self.persona_id = persona_id
        self.total_caracteres = total_caracteres
        super().__init__(
            f"Corpus insuficiente para persona {persona_id}: "
            f"{total_caracteres} chars (mínimo 3 000)"
        )


class CorpusPreparador:
    """
    TODO Fase D: preparar el corpus textual de una persona desde la DB.

    Uso esperado:
        preparador = CorpusPreparador()
        corpus = await preparador.preparar(persona_id, session)
    """

    async def preparar(
        self,
        persona_id: uuid.UUID,
        session: Any,  # AsyncSession — Any para no importar SQLAlchemy en stubs
    ) -> CorpusPreparado:
        """TODO Fase D: consultar papers + documentos_corpus, aplicar pesos y estratificación."""
        raise NotImplementedError("TODO Fase D: implementar CorpusPreparador.preparar")
