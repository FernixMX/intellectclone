"""
Cliente Anthropic Claude para IntellectClone.
TODO Fase D: implementar con anthropic SDK según docs/05_perfilador_y_gemelo.md §D1.

Pases que usarán ClaudeClient por default: hexaco, schwartz, posturas.
Modelo default: claude-sonnet-4-6 (R8).
"""

from __future__ import annotations

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.llm.tipos import ResultadoLLM


class ClaudeClient(ClienteLLMBase):
    """
    TODO Fase D: cliente real para la API de Anthropic Claude.

    Responsabilidades:
    - Registrar tokens_prompt, tokens_completion, costo_usd, duracion_ms por llamada
    - Calcular costo USD según tabla de precios por modelo
    - Propagar LLMErrorProveedor ante errores de la API
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = api_key
        self._model = model

    async def completar(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> ResultadoLLM:
        """TODO Fase D: llamar anthropic.AsyncAnthropic.messages.create()."""
        raise NotImplementedError("TODO Fase D: implementar ClaudeClient.completar")
