"""
Stub de cliente OpenAI para IntellectClone v1.
No implementado en v1 — se activa en versiones futuras si se requiere.
"""

from __future__ import annotations

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.llm.tipos import ResultadoLLM


class OpenAIClient(ClienteLLMBase):
    """Stub de cliente OpenAI. No implementado en v1."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._model = model

    async def completar(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> ResultadoLLM:
        raise NotImplementedError(
            "OpenAIClient no está implementado en v1. Proveedor 'openai' no disponible."
        )
