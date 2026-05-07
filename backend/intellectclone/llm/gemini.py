"""
Cliente Google Gemini para IntellectClone.
TODO Fase D: implementar con google-genai SDK según docs/05_perfilador_y_gemelo.md §D1.

Pases que usarán GeminiClient por default: idiolecto, validacion.
Modelo default: gemini-2.5-flash.
"""

from __future__ import annotations

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.llm.tipos import ResultadoLLM


class GeminiClient(ClienteLLMBase):
    """
    TODO Fase D: cliente real para la API de Google Gemini.

    Responsabilidades:
    - Registrar tokens_prompt, tokens_completion, costo_usd, duracion_ms por llamada
    - Usar genai.Client(api_key=...).aio.models.generate_content()
    - Propagat LLMErrorProveedor ante errores de la API
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._api_key = api_key
        self._model = model

    async def completar(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> ResultadoLLM:
        """TODO Fase D: llamar google.genai.Client.aio.models.generate_content()."""
        raise NotImplementedError("TODO Fase D: implementar GeminiClient.completar")
