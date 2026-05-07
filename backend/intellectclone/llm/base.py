"""
Clase base abstracta para clientes LLM.
TODO Fase D: implementar completar_json con retry según docs/05_perfilador_y_gemelo.md §D1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from intellectclone.llm.tipos import ResultadoLLM


class ClienteLLMBase(ABC):
    """
    Interfaz base para todos los clientes LLM de IntellectClone.

    TODO Fase D — métodos a implementar:
    - completar(): llamada base al proveedor, devuelve ResultadoLLM
    - completar_json(): retry con re-prompt ante JSON malformado (máx 2 reintentos),
      lanza LLMJsonMalformado si se agotan los intentos
    """

    @abstractmethod
    async def completar(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> ResultadoLLM:
        """Ejecuta una llamada de completado y devuelve el resultado con observabilidad."""
        ...

    async def completar_json(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
        max_reintentos: int = 2,
    ) -> tuple[dict[str, Any], ResultadoLLM]:
        """
        TODO Fase D: llamar completar() parseando resultado como JSON.
        Retry con re-prompt ante JSON malformado; máximo max_reintentos veces.
        Lanza LLMJsonMalformado si se agotan todos los intentos.
        """
        raise NotImplementedError("TODO Fase D: implementar completar_json con retry logic")
