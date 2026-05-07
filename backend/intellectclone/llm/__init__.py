"""
Capa LLM de IntellectClone.
TODO Fase D: clientes reales y router según docs/05_perfilador_y_gemelo.md §D1.
"""

from intellectclone.llm.base import ClienteLLMBase
from intellectclone.llm.claude import ClaudeClient
from intellectclone.llm.gemini import GeminiClient
from intellectclone.llm.openai_stub import OpenAIClient
from intellectclone.llm.router import NOMBRES_PASE, ConfigPase, LLMRouter
from intellectclone.llm.tipos import LLMErrorProveedor, LLMJsonMalformado, ResultadoLLM

__all__ = [
    "ClienteLLMBase",
    "ClaudeClient",
    "GeminiClient",
    "OpenAIClient",
    "ConfigPase",
    "LLMRouter",
    "NOMBRES_PASE",
    "LLMErrorProveedor",
    "LLMJsonMalformado",
    "ResultadoLLM",
]
