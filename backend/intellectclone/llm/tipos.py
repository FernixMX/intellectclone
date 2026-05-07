"""
Tipos compartidos de la capa LLM de IntellectClone.
TODO Fase D: implementar clientes reales según docs/05_perfilador_y_gemelo.md §10.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoLLM:
    """Resultado de una llamada a un LLM con observabilidad completa."""

    texto: str
    tokens_prompt: int
    tokens_completion: int
    costo_usd: float
    duracion_ms: int
    modelo: str

    @property
    def tokens_total(self) -> int:
        return self.tokens_prompt + self.tokens_completion


class LLMJsonMalformado(Exception):
    """Se lanza cuando el LLM no devuelve JSON válido tras todos los reintentos."""

    def __init__(self, intentos: int, ultimo_error: str) -> None:
        self.intentos = intentos
        self.ultimo_error = ultimo_error
        super().__init__(f"JSON inválido tras {intentos} intento(s). Último error: {ultimo_error}")


class LLMErrorProveedor(Exception):
    """Se lanza ante errores de red o autenticación de la API del proveedor LLM."""

    def __init__(self, proveedor: str, mensaje: str) -> None:
        self.proveedor = proveedor
        self.mensaje = mensaje
        super().__init__(f"Error del proveedor {proveedor!r}: {mensaje}")
