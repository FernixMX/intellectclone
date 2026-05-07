"""
Tests unitarios para RIUATHarvester (C6).

Cubre:
- _mapear_tipo_riuat: tipos conocidos y desconocido
- _extraer_handle: extracción de handle desde URL/URN
- _extraer_doi_de_identifiers: con y sin DOI en lista
- _año_de_fecha: parseo de año desde cadena de fecha
- parsear_oai_record: registro completo, deleted, sin metadata, tesis
- parsear_html_handle: página con table, sin table, sin título
- parsear_registro: conversión al formato canónico
- cosechar (OAI): dos páginas con resumptionToken, para en última
- cosechar (OAI): noRecordsMatch → break limpio sin error
- cosechar (OAI): 503 → _OAINoDisponible → fallback HTML
- cosechar (OAI): XML inválido → _OAINoDisponible → fallback HTML
- cosechar (HTML): itera handles, salta 404, salta errores de red
- health_check: 200 OK y excepción de red
- auto-registro en registry
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from intellectclone.harvesters.riuat import (
    RIUATHarvester,
    _año_de_fecha,
    _extraer_doi_de_identifiers,
    _extraer_handle,
    _mapear_tipo_riuat,
    parsear_html_handle,
    parsear_oai_record,
)
from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

# ---------------------------------------------------------------------------
# Rutas a fixtures
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _xml(nombre: str) -> str:
    return (_FIXTURES / nombre).read_text(encoding="utf-8")


def _html(nombre: str) -> str:
    return (_FIXTURES / nombre).read_text(encoding="utf-8")


def _soup_html(nombre: str) -> BeautifulSoup:
    return BeautifulSoup(_html(nombre), "html.parser")


# ---------------------------------------------------------------------------
# Helper: cliente async mock
# ---------------------------------------------------------------------------


def _mk_response(text: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=MagicMock()
        )
    return resp


def _mk_async_client(*responses: MagicMock) -> MagicMock:
    """Mock que simula AsyncClient como context manager devolviendo respuestas en orden."""
    client = MagicMock()
    get_mock = AsyncMock(side_effect=list(responses))
    client.get = get_mock
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ---------------------------------------------------------------------------
# Fixture de harvester configurado
# ---------------------------------------------------------------------------


@pytest.fixture()
def harvester() -> RIUATHarvester:
    h = RIUATHarvester()
    h.configurar(
        {
            "base_url": "https://riuat.test",
            "handle_inicio": 1,
            "handle_fin": 5,
        }
    )
    return h


# ---------------------------------------------------------------------------
# Tests: _mapear_tipo_riuat
# ---------------------------------------------------------------------------


class TestMapearTipoRiuat:
    def test_article_ingles(self) -> None:
        assert _mapear_tipo_riuat("article") == TipoPaper.articulo.value

    def test_articulo_espanol(self) -> None:
        assert _mapear_tipo_riuat("artículo") == TipoPaper.articulo.value

    def test_journal_article(self) -> None:
        assert _mapear_tipo_riuat("Journal Article") == TipoPaper.articulo.value

    def test_tesis_maestria(self) -> None:
        assert _mapear_tipo_riuat("Tesis de Maestría") == TipoPaper.tesis_maestria.value

    def test_tesis_doctorado(self) -> None:
        assert _mapear_tipo_riuat("Tesis Doctoral") == TipoPaper.tesis_doctorado.value

    def test_tesis_licenciatura(self) -> None:
        assert _mapear_tipo_riuat("Tesis de Licenciatura") == TipoPaper.tesis_licenciatura.value

    def test_libro(self) -> None:
        assert _mapear_tipo_riuat("libro") == TipoPaper.libro.value

    def test_conference_paper(self) -> None:
        assert _mapear_tipo_riuat("conference paper") == TipoPaper.memoria_congreso.value

    def test_desconocido(self) -> None:
        assert _mapear_tipo_riuat("patente") == TipoPaper.otro.value

    def test_vacio(self) -> None:
        assert _mapear_tipo_riuat("") == TipoPaper.otro.value


# ---------------------------------------------------------------------------
# Tests: _extraer_handle
# ---------------------------------------------------------------------------


class TestExtraerHandle:
    def test_url_completa(self) -> None:
        assert _extraer_handle("https://riuat.uat.edu.mx/handle/123456789/42") == "123456789/42"

    def test_urn(self) -> None:
        assert _extraer_handle("hdl:123456789/55") == "123456789/55"

    def test_solo_path(self) -> None:
        assert _extraer_handle("123456789/78") == "123456789/78"

    def test_sin_patron(self) -> None:
        assert _extraer_handle("https://doi.org/10.1016/j.nano.2022.42") is None


# ---------------------------------------------------------------------------
# Tests: _extraer_doi_de_identifiers
# ---------------------------------------------------------------------------


class TestExtraerDoiDeIdentifiers:
    def test_doi_en_url(self) -> None:
        result = _extraer_doi_de_identifiers(
            [
                "https://riuat.uat.edu.mx/handle/123456789/42",
                "https://doi.org/10.1016/j.nano.2022.42",
            ]
        )
        assert result is not None
        assert "10.1016/j.nano.2022.42" in result

    def test_doi_normalizado(self) -> None:
        result = _extraer_doi_de_identifiers(["https://doi.org/10.1016/j.science.2021.001"])
        assert result is not None
        assert result.startswith("10.")

    def test_sin_doi(self) -> None:
        result = _extraer_doi_de_identifiers(
            [
                "https://riuat.uat.edu.mx/handle/123456789/55",
            ]
        )
        assert result is None

    def test_lista_vacia(self) -> None:
        assert _extraer_doi_de_identifiers([]) is None


# ---------------------------------------------------------------------------
# Tests: _año_de_fecha
# ---------------------------------------------------------------------------


class TestAñoDeFecha:
    def test_fecha_iso(self) -> None:
        assert _año_de_fecha("2022-03-10") == 2022

    def test_solo_año(self) -> None:
        assert _año_de_fecha("2021") == 2021

    def test_texto_con_año(self) -> None:
        assert _año_de_fecha("Publicado en 2020") == 2020

    def test_sin_año(self) -> None:
        assert _año_de_fecha("sin fecha") is None


# ---------------------------------------------------------------------------
# Tests: parsear_oai_record
# ---------------------------------------------------------------------------


class TestParsearOaiRecord:
    def _record_from_xml(self, page: str, idx: int) -> ET.Element:
        """Extrae el idx-ésimo <record> del XML de fixtures."""
        root = ET.fromstring(_xml(page))
        ns = {"oai": "http://www.openarchives.org/OAI/2.0/"}
        records = root.find("oai:ListRecords", ns)
        assert records is not None
        return list(records.findall("oai:record", ns))[idx]

    def test_registro_completo(self) -> None:
        record_el = self._record_from_xml("riuat_oai_page1.xml", 0)
        datos = parsear_oai_record(record_el)
        assert datos is not None
        assert "nanotecnología" in datos["titulo"]
        assert datos["handle_riuat"] == "123456789/42"
        assert datos["doi"] is not None
        assert datos["año"] == 2022
        assert datos["autores_texto"] == "García López, Juan; Martínez Reyes, Ana"
        assert datos["directores_texto"] is None  # no es tesis
        assert datos["abstract_texto"] is not None
        assert datos["fuente_origen"] == TipoFuente.riuat.value

    def test_registro_deleted_retorna_none(self) -> None:
        record_el = self._record_from_xml("riuat_oai_page1.xml", 1)
        assert parsear_oai_record(record_el) is None

    def test_tesis_tiene_directores(self) -> None:
        record_el = self._record_from_xml("riuat_oai_page2.xml", 0)
        datos = parsear_oai_record(record_el)
        assert datos is not None
        assert datos["tipo"] == TipoPaper.tesis_maestria.value
        assert datos["es_tesis"] is True
        assert datos["autores_texto"] == "López Hernández, María"
        assert datos["directores_texto"] == "Pérez Torres, Carlos; Ramírez Castro, Luisa"

    def test_registro_sin_handle(self) -> None:
        """Registro sin dc:identifier de handle → handle_riuat es None."""
        xml_str = """<?xml version="1.0"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords>
    <record>
      <header><identifier>oai:test:1</identifier><datestamp>2024-01-01</datestamp></header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Sin Handle</dc:title>
          <dc:type>Article</dc:type>
          <dc:date>2024</dc:date>
        </oai_dc:dc>
      </metadata>
    </record>
  </ListRecords>
</OAI-PMH>"""
        root = ET.fromstring(xml_str)
        ns = {"oai": "http://www.openarchives.org/OAI/2.0/"}
        record_el = root.find("oai:ListRecords/oai:record", ns)
        assert record_el is not None
        datos = parsear_oai_record(record_el)
        assert datos is not None
        assert datos["handle_riuat"] is None

    def test_registro_sin_metadata_retorna_none(self) -> None:
        xml_str = """<?xml version="1.0"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords>
    <record>
      <header><identifier>oai:test:99</identifier><datestamp>2024-01-01</datestamp></header>
    </record>
  </ListRecords>
</OAI-PMH>"""
        root = ET.fromstring(xml_str)
        ns = {"oai": "http://www.openarchives.org/OAI/2.0/"}
        record_el = root.find("oai:ListRecords/oai:record", ns)
        assert record_el is not None
        assert parsear_oai_record(record_el) is None


# ---------------------------------------------------------------------------
# Tests: parsear_html_handle
# ---------------------------------------------------------------------------


class TestParsearHtmlHandle:
    def test_pagina_completa(self) -> None:
        soup = _soup_html("riuat_html_handle.html")
        datos = parsear_html_handle(soup, "123456789/55")
        assert datos is not None
        assert "climáticas" in datos["titulo"]
        assert datos["handle_riuat"] == "123456789/55"
        assert datos["año"] == 2021
        assert datos["tipo"] == TipoPaper.articulo.value
        assert datos["idioma"] == "es"
        assert datos["abstract_texto"] is not None
        assert "Rodríguez Sánchez, Pedro" in datos["autores_texto"]  # type: ignore[operator]
        assert datos["fuente_origen"] == TipoFuente.riuat.value

    def test_sin_tabla_retorna_none(self) -> None:
        soup = BeautifulSoup("<html><body><p>nada</p></body></html>", "html.parser")
        assert parsear_html_handle(soup, "123456789/99") is None

    def test_tabla_sin_titulo_retorna_none(self) -> None:
        html = """<html><body>
<table class="itemDisplayTable">
  <tr>
    <td class="metadataFieldLabel">dc.type</td>
    <td class="metadataFieldValue">Article</td>
  </tr>
</table></body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        assert parsear_html_handle(soup, "123456789/99") is None

    def test_dos_autores(self) -> None:
        soup = _soup_html("riuat_html_handle.html")
        datos = parsear_html_handle(soup, "123456789/55")
        assert datos is not None
        assert "Flores Medina, Carmen" in datos["autores_texto"]  # type: ignore[operator]

    def test_tesis_html_directores(self) -> None:
        html = """<html><body>
<table class="itemDisplayTable">
  <tr>
    <td class="metadataFieldLabel">dc.title</td>
    <td class="metadataFieldValue">Mi Tesis de Maestría</td>
  </tr>
  <tr>
    <td class="metadataFieldLabel">dc.contributor.author</td>
    <td class="metadataFieldValue">Alumno, Pedro</td>
  </tr>
  <tr>
    <td class="metadataFieldLabel">dc.contributor.advisor</td>
    <td class="metadataFieldValue">Director, Juan</td>
  </tr>
  <tr>
    <td class="metadataFieldLabel">dc.type</td>
    <td class="metadataFieldValue">Tesis de Maestría</td>
  </tr>
  <tr>
    <td class="metadataFieldLabel">dc.date.issued</td>
    <td class="metadataFieldValue">2023-05</td>
  </tr>
</table>
</body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        datos = parsear_html_handle(soup, "123456789/101")
        assert datos is not None
        assert datos["tipo"] == TipoPaper.tesis_maestria.value
        assert datos["es_tesis"] is True
        assert datos["directores_texto"] == "Director, Juan"
        assert datos["autores_texto"] == "Alumno, Pedro"


# ---------------------------------------------------------------------------
# Tests: parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistro:
    def test_formato_canonico_completo(self, harvester: RIUATHarvester) -> None:
        raw: dict[str, Any] = {
            "handle_riuat": "123456789/42",
            "oai_identifier": "oai:riuat.uat.edu.mx:123456789/42",
            "doi": "10.1016/j.nano.2022.42",
            "titulo": "Título de prueba",
            "titulo_normalizado": "titulo de prueba",
            "autores_texto": "García, Juan",
            "directores_texto": None,
            "abstract_texto": "Resumen breve.",
            "año": 2022,
            "fecha_publicacion": "2022-03-10",
            "idioma": "es",
            "tipo": TipoPaper.articulo.value,
            "es_tesis": False,
            "fuente_origen": TipoFuente.riuat.value,
        }
        parsed = harvester.parsear_registro(raw)
        assert parsed["fuente_origen"] == TipoFuente.riuat.value
        assert parsed["handle_riuat"] == "123456789/42"
        assert parsed["doi"] == "10.1016/j.nano.2022.42"
        assert parsed["es_tesis"] is False

    def test_tipo_default_otro(self, harvester: RIUATHarvester) -> None:
        parsed = harvester.parsear_registro({"titulo": "X"})
        assert parsed["tipo"] == TipoPaper.otro.value

    def test_es_tesis_default_false(self, harvester: RIUATHarvester) -> None:
        parsed = harvester.parsear_registro({"titulo": "X"})
        assert parsed["es_tesis"] is False


# ---------------------------------------------------------------------------
# Tests: cosechar (OAI) — dos páginas con resumptionToken
# ---------------------------------------------------------------------------


class TestCosecharOai:
    @pytest.mark.asyncio
    async def test_dos_paginas_resumption_token(self, harvester: RIUATHarvester) -> None:
        """Debe cosechar page1 (2 records válidos + 1 deleted) y page2 (1 tesis)."""
        resp1 = _mk_response(_xml("riuat_oai_page1.xml"))
        resp2 = _mk_response(_xml("riuat_oai_page2.xml"))
        client_mock = _mk_async_client(resp1, resp2)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-1", "completo", {}):
                resultados.append(r)

        # page1: 2 válidos (deleted se salta), page2: 1 tesis → total 3
        assert len(resultados) == 3
        handles = [r.datos.get("handle_riuat") for r in resultados]
        assert "123456789/42" in handles
        assert "123456789/55" in handles
        assert "123456789/78" in handles

    @pytest.mark.asyncio
    async def test_tesis_en_resultado_tiene_directores(self, harvester: RIUATHarvester) -> None:
        resp1 = _mk_response(_xml("riuat_oai_page1.xml"))
        resp2 = _mk_response(_xml("riuat_oai_page2.xml"))
        client_mock = _mk_async_client(resp1, resp2)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-1", "completo", {}):
                resultados.append(r)

        tesis = next(r for r in resultados if r.datos.get("handle_riuat") == "123456789/78")
        assert tesis.datos["es_tesis"] is True
        assert tesis.datos["directores_texto"] is not None

    @pytest.mark.asyncio
    async def test_no_records_match_para_limpio(self, harvester: RIUATHarvester) -> None:
        """noRecordsMatch debe terminar sin error y sin registros."""
        resp = _mk_response(_xml("riuat_oai_no_records.xml"))
        client_mock = _mk_async_client(resp)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-2", "completo", {}):
                resultados.append(r)

        assert resultados == []

    @pytest.mark.asyncio
    async def test_503_dispara_fallback_html(self, harvester: RIUATHarvester) -> None:
        """503 en OAI → _OAINoDisponible → fallback HTML (handles 1..5)."""
        resp_503 = _mk_response("Service Unavailable", status_code=503)
        # HTML fallback: todos 404 para simplificar
        resp_404 = _mk_response("Not Found", status_code=404)
        client_mock = _mk_async_client(resp_503, *[resp_404] * 5)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-3", "completo", {}):
                resultados.append(r)

        # 503 → fallback → todos 404 → sin resultados (pero sin excepción)
        assert resultados == []

    @pytest.mark.asyncio
    async def test_xml_invalido_dispara_fallback_html(self, harvester: RIUATHarvester) -> None:
        """XML inválido en respuesta OAI → fallback HTML."""
        resp_bad_xml = _mk_response("<<< not xml >>>")
        resp_404 = _mk_response("Not Found", status_code=404)
        client_mock = _mk_async_client(resp_bad_xml, *[resp_404] * 5)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-4", "completo", {}):
                resultados.append(r)

        assert resultados == []

    @pytest.mark.asyncio
    async def test_fuente_id_usa_handle(self, harvester: RIUATHarvester) -> None:
        resp = _mk_response(_xml("riuat_oai_page1.xml"))
        # page2 vacía (sin resumptionToken)
        xml_vacio = """<?xml version="1.0"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords><resumptionToken/></ListRecords>
</OAI-PMH>"""
        resp2 = _mk_response(xml_vacio)
        client_mock = _mk_async_client(resp, resp2)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-5", "completo", {}):
                resultados.append(r)

        for r in resultados:
            assert r.fuente_id != ""


# ---------------------------------------------------------------------------
# Tests: cosechar (HTML fallback)
# ---------------------------------------------------------------------------


class TestCosecharHtml:
    @pytest.fixture()
    def harvester_html(self) -> RIUATHarvester:
        h = RIUATHarvester()
        h.configurar(
            {
                "base_url": "https://riuat.test",
                "preferir_oai": False,
                "handle_inicio": 55,
                "handle_fin": 57,
            }
        )
        return h

    @pytest.mark.asyncio
    async def test_itera_handles_y_parsea_validos(self, harvester_html: RIUATHarvester) -> None:
        resp_html = _mk_response(_html("riuat_html_handle.html"))
        resp_404 = _mk_response("Not Found", status_code=404)
        resp_html2 = _mk_response("Not Found", status_code=404)
        client_mock = _mk_async_client(resp_html, resp_404, resp_html2)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester_html.cosechar("cosecha-h1", "completo", {}):
                resultados.append(r)

        # handle 55 → válido, 56 → 404 skip, 57 → 404 skip
        assert len(resultados) == 1
        assert resultados[0].datos["handle_riuat"] is not None

    @pytest.mark.asyncio
    async def test_error_red_se_salta(self, harvester_html: RIUATHarvester) -> None:
        """Error de conexión en un handle no detiene la iteración."""
        import httpx

        client_mock = MagicMock()
        client_mock.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester_html.cosechar("cosecha-h2", "completo", {}):
                resultados.append(r)

        assert resultados == []  # sin crash, sin resultados

    @pytest.mark.asyncio
    async def test_parametros_override_handle_range(self, harvester_html: RIUATHarvester) -> None:
        """Los parametros pueden sobreescribir handle_inicio/handle_fin."""
        resp_404 = _mk_response("Not Found", status_code=404)
        # Solo 2 handles: 10 y 11
        client_mock = _mk_async_client(resp_404, resp_404)

        with (
            patch("intellectclone.harvesters.riuat.asyncio.sleep", new_callable=AsyncMock),
            patch("intellectclone.harvesters.riuat.httpx.AsyncClient", return_value=client_mock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester_html.cosechar(
                "cosecha-h3", "completo", {"handle_inicio": 10, "handle_fin": 11}
            ):
                resultados.append(r)

        assert client_mock.get.call_count == 2


# ---------------------------------------------------------------------------
# Tests: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_retorna_true_con_200(self, harvester: RIUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("intellectclone.harvesters.riuat.httpx.get", return_value=resp):
            assert harvester.health_check() is True

    def test_retorna_false_con_503(self, harvester: RIUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 503
        with patch("intellectclone.harvesters.riuat.httpx.get", return_value=resp):
            assert harvester.health_check() is False

    def test_retorna_false_en_excepcion(self, harvester: RIUATHarvester) -> None:
        import httpx

        with patch(
            "intellectclone.harvesters.riuat.httpx.get", side_effect=httpx.ConnectError("err")
        ):
            assert harvester.health_check() is False


# ---------------------------------------------------------------------------
# Tests: auto-registro
# ---------------------------------------------------------------------------


class TestAutoRegistro:
    def test_riuat_registrado_en_registry(self) -> None:
        import intellectclone.harvesters.riuat  # noqa: F401 — fuerza importación
        from intellectclone.models.enums import TipoFuente

        harvester_cls = obtener_harvester(TipoFuente.riuat.value)
        assert harvester_cls is RIUATHarvester

    def test_fuente_tipo(self) -> None:
        assert RIUATHarvester.fuente_tipo == TipoFuente.riuat.value
