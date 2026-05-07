"""
Tests unitarios para ORCIDEnricher (C7).

Cubre:
- validar_formato_orcid: formato válido e inválido
- validar_checksum_orcid: checksum correcto e incorrecto
- validar_orcid: compuesto de formato + checksum
- _extraer_doi_de_external_ids: con DOI y sin DOI
- _extraer_año_orcid: con fecha y sin fecha
- parsear_work_orcid: work completo, sin título (→ None), sin DOI, sin fecha
- parsear_registro: conversión al formato canónico
- cosechar: ORCID inválido → sin resultados
- cosechar: dos works válidos + uno sin título (salta)
- cosechar: 404 en API → raise_for_status lanza excepción
- cosechar: confianza_match presente en resultados
- health_check: 200 OK y excepción de red
- auto-registro en registry
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellectclone.harvesters.orcid_enricher import (
    ORCIDEnricher,
    _extraer_año_orcid,
    _extraer_doi_de_external_ids,
    parsear_work_orcid,
    validar_checksum_orcid,
    validar_formato_orcid,
    validar_orcid,
)
from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "fixtures"
_ORCID_VALIDO = "0000-0001-5109-3700"
_ORCID_INVALIDO_FORMATO = "0000-0001-5109"
_ORCID_INVALIDO_CHECKSUM = "0000-0001-5109-3701"


def _load_orcid_works() -> dict[str, Any]:
    return json.loads((_FIXTURES / "orcid_works.json").read_text())


def _mk_response(payload: Any, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=payload)
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=MagicMock()
        )
    return resp


def _mk_async_client(resp: MagicMock) -> MagicMock:
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture()
def enricher() -> ORCIDEnricher:
    e = ORCIDEnricher()
    e.configurar({"base_url": "https://pub.orcid.test", "mailto": "test@uat.edu.mx"})
    return e


# ---------------------------------------------------------------------------
# Tests: validar_formato_orcid
# ---------------------------------------------------------------------------


class TestValidarFormatoOrcid:
    def test_formato_valido(self) -> None:
        assert validar_formato_orcid("0000-0001-5109-3700") is True

    def test_formato_con_x_final(self) -> None:
        assert validar_formato_orcid("0000-0002-1825-009X") is True

    def test_formato_corto(self) -> None:
        assert validar_formato_orcid("0000-0001-5109") is False

    def test_formato_sin_guiones(self) -> None:
        assert validar_formato_orcid("0000000151093700") is False

    def test_formato_letras_en_medio(self) -> None:
        assert validar_formato_orcid("ABCD-0001-5109-3700") is False

    def test_formato_vacio(self) -> None:
        assert validar_formato_orcid("") is False


# ---------------------------------------------------------------------------
# Tests: validar_checksum_orcid
# ---------------------------------------------------------------------------


class TestValidarChecksumOrcid:
    def test_checksum_correcto(self) -> None:
        assert validar_checksum_orcid("0000-0001-5109-3700") is True

    def test_checksum_correcto_x(self) -> None:
        assert validar_checksum_orcid("0000-0002-1825-0097") is True

    def test_checksum_incorrecto(self) -> None:
        assert validar_checksum_orcid("0000-0001-5109-3701") is False

    def test_longitud_incorrecta(self) -> None:
        assert validar_checksum_orcid("0000-0001-5109") is False


# ---------------------------------------------------------------------------
# Tests: validar_orcid (compuesto)
# ---------------------------------------------------------------------------


class TestValidarOrcid:
    def test_orcid_valido_completo(self) -> None:
        assert validar_orcid(_ORCID_VALIDO) is True

    def test_formato_invalido(self) -> None:
        assert validar_orcid(_ORCID_INVALIDO_FORMATO) is False

    def test_checksum_invalido(self) -> None:
        assert validar_orcid(_ORCID_INVALIDO_CHECKSUM) is False

    def test_vacio(self) -> None:
        assert validar_orcid("") is False


# ---------------------------------------------------------------------------
# Tests: _extraer_doi_de_external_ids
# ---------------------------------------------------------------------------


class TestExtraerDoiDeExternalIds:
    def test_doi_presente(self) -> None:
        ext_ids = [
            {"external-id-type": "pmid", "external-id-value": "12345678"},
            {"external-id-type": "doi", "external-id-value": "10.1016/j.nano.2022.42"},
        ]
        result = _extraer_doi_de_external_ids(ext_ids)
        assert result is not None
        assert "10.1016/j.nano.2022.42" in result

    def test_doi_como_url_normalizado(self) -> None:
        ext_ids = [
            {
                "external-id-type": "doi",
                "external-id-value": "https://doi.org/10.1016/j.nano.2022.42",
            }
        ]
        result = _extraer_doi_de_external_ids(ext_ids)
        assert result is not None
        assert not result.startswith("https")

    def test_sin_doi(self) -> None:
        ext_ids = [{"external-id-type": "pmid", "external-id-value": "12345678"}]
        assert _extraer_doi_de_external_ids(ext_ids) is None

    def test_lista_vacia(self) -> None:
        assert _extraer_doi_de_external_ids([]) is None


# ---------------------------------------------------------------------------
# Tests: _extraer_año_orcid
# ---------------------------------------------------------------------------


class TestExtraerAñoOrcid:
    def test_año_presente(self) -> None:
        pub_date = {"year": {"value": "2022"}, "month": {"value": "03"}}
        assert _extraer_año_orcid(pub_date) == 2022

    def test_solo_año(self) -> None:
        pub_date = {"year": {"value": "2021"}, "month": None, "day": None}
        assert _extraer_año_orcid(pub_date) == 2021

    def test_pub_date_none(self) -> None:
        assert _extraer_año_orcid(None) is None

    def test_sin_valor_year(self) -> None:
        pub_date = {"year": None}
        assert _extraer_año_orcid(pub_date) is None


# ---------------------------------------------------------------------------
# Tests: parsear_work_orcid
# ---------------------------------------------------------------------------


class TestParsearWorkOrcid:
    def test_work_completo(self) -> None:
        works = _load_orcid_works()
        summary = works["group"][0]["work-summary"][0]
        datos = parsear_work_orcid(summary, _ORCID_VALIDO)
        assert datos is not None
        assert "nanotecnología" in datos["titulo"]
        assert datos["orcid"] == _ORCID_VALIDO
        assert datos["orcid_put_code"] == 12345
        assert datos["doi"] is not None
        assert datos["año"] == 2022
        assert datos["tipo"] == TipoPaper.articulo.value
        assert datos["revista"] == "Nanomaterials"
        assert datos["confianza_match"] > 0.8
        assert datos["fuente_origen"] == TipoFuente.orcid.value

    def test_work_sin_doi(self) -> None:
        works = _load_orcid_works()
        summary = works["group"][1]["work-summary"][0]
        datos = parsear_work_orcid(summary, _ORCID_VALIDO)
        assert datos is not None
        assert datos["doi"] is None
        assert datos["año"] == 2021

    def test_work_titulo_vacio_retorna_none(self) -> None:
        works = _load_orcid_works()
        summary = works["group"][2]["work-summary"][0]
        assert parsear_work_orcid(summary, _ORCID_VALIDO) is None

    def test_titulo_normalizado_presente(self) -> None:
        works = _load_orcid_works()
        summary = works["group"][0]["work-summary"][0]
        datos = parsear_work_orcid(summary, _ORCID_VALIDO)
        assert datos is not None
        assert datos["titulo_normalizado"] is not None
        assert datos["titulo_normalizado"] != datos["titulo"]


# ---------------------------------------------------------------------------
# Tests: parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistro:
    def test_formato_canonico(self, enricher: ORCIDEnricher) -> None:
        raw: dict[str, Any] = {
            "orcid": _ORCID_VALIDO,
            "orcid_put_code": 12345,
            "doi": "10.1016/j.nano.2022.42",
            "titulo": "Título de prueba",
            "titulo_normalizado": "titulo de prueba",
            "año": 2022,
            "tipo": TipoPaper.articulo.value,
            "revista": "Nanomaterials",
            "confianza_match": 0.95,
        }
        parsed = enricher.parsear_registro(raw)
        assert parsed["fuente_origen"] == TipoFuente.orcid.value
        assert parsed["orcid"] == _ORCID_VALIDO
        assert parsed["confianza_match"] == 0.95

    def test_tipo_default_otro(self, enricher: ORCIDEnricher) -> None:
        parsed = enricher.parsear_registro({"titulo": "X"})
        assert parsed["tipo"] == TipoPaper.otro.value


# ---------------------------------------------------------------------------
# Tests: cosechar
# ---------------------------------------------------------------------------


class TestCosechar:
    @pytest.mark.asyncio
    async def test_orcid_invalido_no_emite(self, enricher: ORCIDEnricher) -> None:
        with patch("intellectclone.harvesters.orcid_enricher.httpx.AsyncClient"):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar(
                "c1", "enriquecimiento", {"orcid": _ORCID_INVALIDO_FORMATO}
            ):
                resultados.append(r)
        assert resultados == []

    @pytest.mark.asyncio
    async def test_dos_works_validos_uno_sin_titulo(self, enricher: ORCIDEnricher) -> None:
        """3 grupos en fixture: 2 válidos + 1 sin título → 2 resultados."""
        payload = _load_orcid_works()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch("intellectclone.harvesters.orcid_enricher.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "intellectclone.harvesters.orcid_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c2", "enriquecimiento", {"orcid": _ORCID_VALIDO}):
                resultados.append(r)

        assert len(resultados) == 2

    @pytest.mark.asyncio
    async def test_confianza_match_en_resultados(self, enricher: ORCIDEnricher) -> None:
        payload = _load_orcid_works()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch("intellectclone.harvesters.orcid_enricher.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "intellectclone.harvesters.orcid_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c3", "enriquecimiento", {"orcid": _ORCID_VALIDO}):
                resultados.append(r)

        for r in resultados:
            assert r.datos.get("confianza_match", 0) > 0.8

    @pytest.mark.asyncio
    async def test_fuente_id_usa_put_code(self, enricher: ORCIDEnricher) -> None:
        payload = _load_orcid_works()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch("intellectclone.harvesters.orcid_enricher.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "intellectclone.harvesters.orcid_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c4", "enriquecimiento", {"orcid": _ORCID_VALIDO}):
                resultados.append(r)

        assert all(r.fuente_id != "" for r in resultados)

    @pytest.mark.asyncio
    async def test_error_http_propaga_excepcion(self, enricher: ORCIDEnricher) -> None:
        import httpx

        resp = _mk_response({}, status_code=500)
        client_mock = _mk_async_client(resp)

        with (
            patch("intellectclone.harvesters.orcid_enricher.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "intellectclone.harvesters.orcid_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
            pytest.raises(httpx.HTTPStatusError),
        ):
            async for _ in enricher.cosechar("c5", "enriquecimiento", {"orcid": _ORCID_VALIDO}):
                pass

    @pytest.mark.asyncio
    async def test_orcid_vacio_no_emite(self, enricher: ORCIDEnricher) -> None:
        with patch("intellectclone.harvesters.orcid_enricher.httpx.AsyncClient"):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c6", "enriquecimiento", {}):
                resultados.append(r)
        assert resultados == []


# ---------------------------------------------------------------------------
# Tests: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_retorna_true_con_200(self, enricher: ORCIDEnricher) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("intellectclone.harvesters.orcid_enricher.httpx.get", return_value=resp):
            assert enricher.health_check() is True

    def test_retorna_false_con_404(self, enricher: ORCIDEnricher) -> None:
        resp = MagicMock()
        resp.status_code = 404
        with patch("intellectclone.harvesters.orcid_enricher.httpx.get", return_value=resp):
            assert enricher.health_check() is False

    def test_retorna_false_en_excepcion(self, enricher: ORCIDEnricher) -> None:
        import httpx

        with patch(
            "intellectclone.harvesters.orcid_enricher.httpx.get",
            side_effect=httpx.ConnectError("err"),
        ):
            assert enricher.health_check() is False


# ---------------------------------------------------------------------------
# Tests: auto-registro
# ---------------------------------------------------------------------------


class TestAutoRegistro:
    def test_orcid_registrado_en_registry(self) -> None:
        import intellectclone.harvesters.orcid_enricher  # noqa: F401

        harvester_cls = obtener_harvester(TipoFuente.orcid.value)
        assert harvester_cls is ORCIDEnricher

    def test_fuente_tipo(self) -> None:
        assert ORCIDEnricher.fuente_tipo == TipoFuente.orcid.value
