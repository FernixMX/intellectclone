"""
Tests de stubs reservados para Fase D.
Verifica que los endpoints placeholder devuelvan 501 y que los módulos
llm/ y perfilador/ sean importables sin errores.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from intellectclone.llm import (
    NOMBRES_PASE,
    ClaudeClient,
    ClienteLLMBase,
    ConfigPase,
    GeminiClient,
    LLMErrorProveedor,
    LLMJsonMalformado,
    LLMRouter,
    OpenAIClient,
    ResultadoLLM,
)
from intellectclone.perfilador.alertas import SistemaAlertas
from intellectclone.perfilador.corpus import (
    CorpusPreparador,
    CorpusSuficienteError,
)
from intellectclone.perfilador.pases.hexaco import PaseHexaco
from intellectclone.perfilador.pases.idiolecto import PaseIdiolecto
from intellectclone.perfilador.pases.posturas import PasePosturas
from intellectclone.perfilador.pases.schwartz import PaseSchwartz
from intellectclone.perfilador.scores import CalculadorScores
from intellectclone.perfilador.sintetizador import Sintetizador

# ---------------------------------------------------------------------------
# Importabilidad y tipos del módulo llm/
# ---------------------------------------------------------------------------


def test_resultado_llm_tokens_total() -> None:
    r = ResultadoLLM(
        texto="hola",
        tokens_prompt=100,
        tokens_completion=50,
        costo_usd=0.001,
        duracion_ms=200,
        modelo="anthropic:claude-sonnet-4-6",
    )
    assert r.tokens_total == 150


def test_llm_json_malformado_contiene_intentos() -> None:
    exc = LLMJsonMalformado(intentos=3, ultimo_error="Unexpected token")
    assert "3" in str(exc)
    assert exc.intentos == 3


def test_llm_error_proveedor_contiene_proveedor() -> None:
    exc = LLMErrorProveedor(proveedor="anthropic", mensaje="rate limit")
    assert "anthropic" in str(exc)
    assert exc.proveedor == "anthropic"


def test_nombres_pase_contiene_los_cinco() -> None:
    assert {"hexaco", "schwartz", "idiolecto", "posturas", "validacion"} == NOMBRES_PASE


def test_config_pase_es_inmutable() -> None:
    cfg = ConfigPase(proveedor="anthropic", modelo="claude-sonnet-4-6")
    assert cfg.proveedor == "anthropic"
    assert cfg.max_tokens == 4096


def test_llm_router_get_config_pases_validos() -> None:
    router = LLMRouter(anthropic_api_key="x", gemini_api_key="y")
    for pase in NOMBRES_PASE:
        cfg = router.get_config(pase)
        assert isinstance(cfg, ConfigPase)
        assert cfg.proveedor in {"anthropic", "gemini", "openai"}


def test_llm_router_get_config_pase_desconocido() -> None:
    router = LLMRouter(anthropic_api_key="x", gemini_api_key="y")
    with pytest.raises(KeyError):
        router.get_config("pase_inventado")


def test_llm_router_get_config_override() -> None:
    config_custom = {"hexaco": ConfigPase(proveedor="gemini", modelo="gemini-2.5-pro")}
    router = LLMRouter(
        anthropic_api_key="x",
        gemini_api_key="y",
        config_pases=config_custom,
    )
    assert router.get_config("hexaco").modelo == "gemini-2.5-pro"


def test_llm_router_get_cliente_es_stub() -> None:
    router = LLMRouter(anthropic_api_key="x", gemini_api_key="y")
    with pytest.raises(NotImplementedError):
        router.get_cliente("hexaco")


@pytest.mark.asyncio
async def test_claude_client_es_stub() -> None:
    cliente = ClaudeClient(api_key="fake", model="claude-sonnet-4-6")
    with pytest.raises(NotImplementedError):
        await cliente.completar("sys", "user")


@pytest.mark.asyncio
async def test_gemini_client_es_stub() -> None:
    cliente = GeminiClient(api_key="fake", model="gemini-2.5-flash")
    with pytest.raises(NotImplementedError):
        await cliente.completar("sys", "user")


@pytest.mark.asyncio
async def test_openai_client_raises_not_implemented() -> None:
    cliente = OpenAIClient(api_key="fake")
    with pytest.raises(NotImplementedError):
        await cliente.completar("sys", "user")


@pytest.mark.asyncio
async def test_completar_json_es_stub() -> None:
    cliente = ClaudeClient(api_key="fake")
    with pytest.raises(NotImplementedError):
        await cliente.completar_json("sys", "user")


def test_cliente_llm_base_es_abstracto() -> None:
    assert issubclass(ClaudeClient, ClienteLLMBase)
    assert issubclass(GeminiClient, ClienteLLMBase)
    assert issubclass(OpenAIClient, ClienteLLMBase)


# ---------------------------------------------------------------------------
# Importabilidad de módulos perfilador/
# ---------------------------------------------------------------------------


def test_corpus_preparador_es_stub() -> None:
    prep = CorpusPreparador()
    assert prep is not None


def test_corpus_suficiente_error_mensaje() -> None:
    import uuid

    pid = uuid.uuid4()
    exc = CorpusSuficienteError(persona_id=pid, total_caracteres=500)
    assert "500" in str(exc)
    assert str(pid) in str(exc)


def test_sintetizador_es_stub() -> None:
    sint = Sintetizador()
    with pytest.raises(NotImplementedError):
        sint.sintetizar({}, {}, {}, {}, {})


def test_calculador_scores_es_stub() -> None:
    calc = CalculadorScores()
    with pytest.raises(NotImplementedError):
        calc.calcular_veracidad(0.8, 0.7, 0.9, 0.6)


def test_pase_hexaco_es_stub() -> None:
    pase = PaseHexaco()
    assert pase is not None


def test_pase_schwartz_es_stub() -> None:
    pase = PaseSchwartz()
    assert pase is not None


def test_pase_idiolecto_es_stub() -> None:
    pase = PaseIdiolecto()
    assert pase is not None


def test_pase_posturas_es_stub() -> None:
    pase = PasePosturas()
    assert pase is not None


def test_sistema_alertas_es_stub() -> None:
    alertas = SistemaAlertas()
    assert alertas is not None


# ---------------------------------------------------------------------------
# Endpoints 501 — gemelos y perfilador
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gemelos_persona_id_devuelve_501(client: AsyncClient) -> None:
    import uuid

    pid = uuid.uuid4()
    response = await client.get(f"/api/v1/gemelos/{pid}")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_gemelos_versiones_devuelve_501(client: AsyncClient) -> None:
    import uuid

    pid = uuid.uuid4()
    response = await client.get(f"/api/v1/gemelos/{pid}/versiones")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_perfilador_generar_devuelve_501(client: AsyncClient) -> None:
    import uuid

    pid = uuid.uuid4()
    response = await client.post(f"/api/v1/perfilador/generar/{pid}")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_perfilador_estado_devuelve_501(client: AsyncClient) -> None:
    response = await client.get("/api/v1/perfilador/estado/tarea-fake-123")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_perfilador_regenerar_devuelve_501(client: AsyncClient) -> None:
    import uuid

    pid = uuid.uuid4()
    response = await client.post(f"/api/v1/perfilador/regenerar/{pid}")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_perfilador_candidatos_devuelve_501(client: AsyncClient) -> None:
    response = await client.get("/api/v1/perfilador/candidatos-regeneracion")
    assert response.status_code == 501
