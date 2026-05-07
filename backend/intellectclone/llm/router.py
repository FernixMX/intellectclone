"""
Router LLM: mapea nombres de pase a clientes configurados.
TODO Fase D: implementar get_cliente() según docs/05_perfilador_y_gemelo.md §D1.

Pases válidos: hexaco, schwartz, idiolecto, posturas, validacion.
Configuración por default (doc 05 §10):
  hexaco    → anthropic / claude-sonnet-4-6
  schwartz  → anthropic / claude-sonnet-4-6
  idiolecto → gemini / gemini-2.5-flash
  posturas  → anthropic / claude-sonnet-4-6
  validacion → gemini / gemini-2.5-flash
"""

from __future__ import annotations

from dataclasses import dataclass, field

from intellectclone.llm.base import ClienteLLMBase

NOMBRES_PASE: frozenset[str] = frozenset(
    {"hexaco", "schwartz", "idiolecto", "posturas", "validacion"}
)


@dataclass(frozen=True)
class ConfigPase:
    """Configuración de modelo LLM para un pase del perfilador."""

    proveedor: str
    modelo: str
    max_tokens: int = field(default=4096)


_CONFIG_PASES_DEFAULT: dict[str, ConfigPase] = {
    "hexaco": ConfigPase(proveedor="anthropic", modelo="claude-sonnet-4-6"),
    "schwartz": ConfigPase(proveedor="anthropic", modelo="claude-sonnet-4-6"),
    "idiolecto": ConfigPase(proveedor="gemini", modelo="gemini-2.5-flash"),
    "posturas": ConfigPase(proveedor="anthropic", modelo="claude-sonnet-4-6"),
    "validacion": ConfigPase(proveedor="gemini", modelo="gemini-2.5-flash"),
}


class LLMRouter:
    """
    Enruta llamadas de pases del perfilador al cliente LLM configurado.
    TODO Fase D: implementar get_cliente() instanciando ClaudeClient / GeminiClient / OpenAIClient.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        gemini_api_key: str,
        openai_api_key: str = "",
        config_pases: dict[str, ConfigPase] | None = None,
    ) -> None:
        self._anthropic_api_key = anthropic_api_key
        self._gemini_api_key = gemini_api_key
        self._openai_api_key = openai_api_key
        self._config_pases: dict[str, ConfigPase] = (
            dict(config_pases) if config_pases else dict(_CONFIG_PASES_DEFAULT)
        )

    def get_config(self, nombre_pase: str) -> ConfigPase:
        if nombre_pase not in self._config_pases:
            raise KeyError(f"Pase desconocido: {nombre_pase!r}. Válidos: {sorted(NOMBRES_PASE)}")
        return self._config_pases[nombre_pase]

    def get_cliente(self, nombre_pase: str) -> ClienteLLMBase:
        """TODO Fase D: instanciar ClaudeClient, GeminiClient u OpenAIClient según proveedor."""
        raise NotImplementedError("TODO Fase D: implementar LLMRouter.get_cliente")
