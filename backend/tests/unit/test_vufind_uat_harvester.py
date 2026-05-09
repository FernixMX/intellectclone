"""
Tests unitarios para VuFindUATHarvester (C5).

Cubre:
- _mapear_tipo_vufind: tipos conocidos y tipo desconocido
- _extraer_doi_de_texto: DOI en texto plano y en URL
- _extraer_record_id: extracción desde path
- _tiene_siguiente_pagina: con y sin enlace siguiente
- parsear_card: card completa y card sin autor/año
- parsear_detalle: detalle completo y detalle mínimo
- parsear_registro: conversión al formato canónico
- cosechar: dos páginas, paginación se detiene sin "siguiente"
- cosechar: sin resultados en primera página
- cosechar: error HTTP en página → raise_for_status
- cosechar con fetch_detalle=True: fetcha detalle y enriquece
- health_check: 200 OK y fallo de red
- auto-registro en registry
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.harvesters.vufind_uat import (
    VuFindUATHarvester,
    _extraer_doi_de_texto,
    _extraer_record_id,
    _mapear_tipo_vufind,
    _tiene_siguiente_pagina,
    parsear_card,
    parsear_detalle,
)
from intellectclone.models.enums import TipoFuente, TipoPaper

# ---------------------------------------------------------------------------
# Rutas a fixtures HTML
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _html(nombre: str) -> str:
    return (_FIXTURES / nombre).read_text(encoding="utf-8")


def _soup(nombre: str) -> BeautifulSoup:
    return BeautifulSoup(_html(nombre), "html.parser")


# ---------------------------------------------------------------------------
# Fixture de harvester configurado
# ---------------------------------------------------------------------------


@pytest.fixture()
def harvester() -> VuFindUATHarvester:
    h = VuFindUATHarvester()
    h.configurar(
        {
            "base_url": "https://publicaciones.uat.edu.mx/vufind",
            "max_paginas_por_corrida": 50,
            "timeout_segundos": 10,
            "fetch_detalle": False,
        }
    )
    return h


# ---------------------------------------------------------------------------
# Helpers de mock HTTP
# ---------------------------------------------------------------------------


def _mk_response(html: str, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.text = html
    if status >= 400:
        import httpx as _httpx

        resp.raise_for_status = MagicMock(
            side_effect=_httpx.HTTPStatusError(
                f"HTTP {status}", request=MagicMock(), response=MagicMock()
            )
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _mk_async_client(*responses: MagicMock) -> AsyncMock:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=list(responses))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


# ---------------------------------------------------------------------------
# Funciones puras
# ---------------------------------------------------------------------------


class TestMapearTipoVufind:
    def test_articulo(self) -> None:
        assert _mapear_tipo_vufind("Artículo") == TipoPaper.articulo.value

    def test_articulo_sin_acento(self) -> None:
        assert _mapear_tipo_vufind("articulo") == TipoPaper.articulo.value

    def test_tesis_doctoral(self) -> None:
        assert _mapear_tipo_vufind("Tesis Doctoral") == TipoPaper.tesis_doctorado.value

    def test_tesis_maestria(self) -> None:
        assert _mapear_tipo_vufind("Tesis de Maestría") == TipoPaper.tesis_maestria.value

    def test_libro(self) -> None:
        assert _mapear_tipo_vufind("Libro") == TipoPaper.libro.value

    def test_tipo_desconocido(self) -> None:
        assert _mapear_tipo_vufind("Informe Técnico Especial") == TipoPaper.otro.value

    def test_mayusculas(self) -> None:
        assert _mapear_tipo_vufind("ARTÍCULO") == TipoPaper.articulo.value

    def test_vacio(self) -> None:
        assert _mapear_tipo_vufind("") == TipoPaper.otro.value


class TestExtraerDoi:
    def test_doi_en_texto_plano(self) -> None:
        assert _extraer_doi_de_texto("DOI: 10.1234/abc.2022") == "10.1234/abc.2022"

    def test_doi_en_url(self) -> None:
        assert _extraer_doi_de_texto("https://doi.org/10.9999/xyz.001") == "10.9999/xyz.001"

    def test_doi_con_puntuacion_final(self) -> None:
        assert _extraer_doi_de_texto("ver 10.1234/abc.2022.") == "10.1234/abc.2022"

    def test_sin_doi(self) -> None:
        assert _extraer_doi_de_texto("Sin DOI disponible") is None

    def test_vacio(self) -> None:
        assert _extraer_doi_de_texto("") is None


class TestExtraerRecordId:
    def test_path_normal(self) -> None:
        assert _extraer_record_id("/vufind/Record/UAT-001") == "UAT-001"

    def test_path_con_slash_final(self) -> None:
        assert _extraer_record_id("/vufind/Record/UAT-001/") == "UAT-001"

    def test_id_numerico(self) -> None:
        assert _extraer_record_id("/vufind/Record/12345") == "12345"

    def test_vacio(self) -> None:
        assert _extraer_record_id("") == ""


class TestTieneSiguientePagina:
    def test_con_rel_next(self) -> None:
        soup = BeautifulSoup('<a href="/page/2" rel="next">Siguiente</a>', "html.parser")
        assert _tiene_siguiente_pagina(soup) is True

    def test_con_texto_siguiente(self) -> None:
        soup = BeautifulSoup('<a href="/page/2">Siguiente</a>', "html.parser")
        assert _tiene_siguiente_pagina(soup) is True

    def test_con_texto_next(self) -> None:
        soup = BeautifulSoup('<a href="/page/2">Next</a>', "html.parser")
        assert _tiene_siguiente_pagina(soup) is True

    def test_sin_siguiente(self) -> None:
        soup = BeautifulSoup("<p>No hay más resultados</p>", "html.parser")
        assert _tiene_siguiente_pagina(soup) is False

    def test_fixture_pagina1_tiene_siguiente(self) -> None:
        assert _tiene_siguiente_pagina(_soup("vufind_pagina1.html")) is True

    def test_fixture_pagina2_no_tiene_siguiente(self) -> None:
        assert _tiene_siguiente_pagina(_soup("vufind_pagina2.html")) is False


# ---------------------------------------------------------------------------
# parsear_card
# ---------------------------------------------------------------------------


class TestParsearCard:
    def test_card_completa_desde_fixture(self) -> None:
        soup = _soup("vufind_pagina1.html")
        # VuFind UAT usa <li class="result">, no <div class="result">
        cards = soup.find_all("li", class_="result")
        assert len(cards) == 2

        datos = parsear_card(cards[0], "https://publicaciones.uat.edu.mx/vufind")

        assert datos["vufind_id"] == "UAT-2022-001"
        assert "Redes Neuronales" in datos["titulo"]
        assert datos["tipo"] == TipoPaper.articulo.value
        assert datos["año"] == 2022
        assert "Cárdenas" in datos["autores_texto"]
        assert datos["fuente_origen"] == TipoFuente.vufind_uat.value

    def test_card_tesis_doctoral(self) -> None:
        soup = _soup("vufind_pagina1.html")
        cards = soup.find_all("li", class_="result")
        datos = parsear_card(cards[1], "https://publicaciones.uat.edu.mx/vufind")

        assert datos["vufind_id"] == "UAT-2021-042"
        assert datos["tipo"] == TipoPaper.tesis_doctorado.value
        assert datos["año"] == 2021

    def test_card_libro_pagina2(self) -> None:
        soup = _soup("vufind_pagina2.html")
        cards = soup.find_all("li", class_="result")
        datos = parsear_card(cards[0], "https://publicaciones.uat.edu.mx/vufind")

        assert datos["vufind_id"] == "UAT-2020-007"
        assert datos["tipo"] == TipoPaper.libro.value
        assert datos["año"] == 2020

    def test_card_sin_year_devuelve_none(self) -> None:
        # parsear_card recibe un Tag aislado; el tag puede ser cualquier elemento
        html = """
        <li class="result">
          <div class="media-body">
            <a class="title" href="/vufind/Record/X-001">Título sin año</a>
            <div class="format">Artículo</div>
          </div>
        </li>"""
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("li", class_="result")
        datos = parsear_card(card, "https://base.example.com")  # type: ignore[arg-type]

        assert datos["año"] is None
        assert datos["autores_texto"] is None

    def test_card_sin_href_da_id_vacio(self) -> None:
        html = """
        <li class="result">
          <div class="media-body">
            <a class="title">Sin href</a>
            <div class="format">Artículo</div>
          </div>
        </li>"""
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("li", class_="result")
        datos = parsear_card(card, "https://base.example.com")  # type: ignore[arg-type]

        assert datos["vufind_id"] == ""

    def test_url_detalle_construida_correctamente(self) -> None:
        soup = _soup("vufind_pagina1.html")
        cards = soup.find_all("li", class_="result")
        datos = parsear_card(cards[0], "https://publicaciones.uat.edu.mx/vufind")

        assert datos["url_detalle"] == (
            "https://publicaciones.uat.edu.mx/vufind/Record/UAT-2022-001"
        )

    def test_titulo_normalizado_presente(self) -> None:
        soup = _soup("vufind_pagina1.html")
        card = soup.find_all("li", class_="result")[0]
        datos = parsear_card(card, "https://publicaciones.uat.edu.mx/vufind")

        assert datos["titulo_normalizado"] is not None
        assert datos["titulo_normalizado"] == datos["titulo_normalizado"].lower()


# ---------------------------------------------------------------------------
# parsear_detalle
# ---------------------------------------------------------------------------


class TestParsearDetalle:
    def test_detalle_completo_desde_fixture(self) -> None:
        soup = _soup("vufind_detalle.html")
        datos = parsear_detalle(soup, "https://publicaciones.uat.edu.mx/vufind", "UAT-2022-001")

        assert datos["vufind_id"] == "UAT-2022-001"
        assert "Redes Neuronales" in datos["titulo"]
        assert datos["año"] == 2022
        assert datos["tipo"] == TipoPaper.articulo.value
        assert datos["doi"] == "10.1234/educiencia.2022.001"
        assert datos["url_landing"] is not None
        assert "pdf" in datos["url_landing"].lower()
        assert datos["revista"] is not None
        assert "EduCiencia" in datos["revista"]
        assert "Cárdenas" in datos["autores_texto"]

    def test_detalle_minimo_sin_doi_ni_fulltext(self) -> None:
        html = """<html><body>
        <h1 class="record-title">Título mínimo</h1>
        <dl>
          <dt>Año</dt><dd>2019</dd>
          <dt>Tipo</dt><dd>Libro</dd>
        </dl>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        datos = parsear_detalle(soup, "https://base.example.com", "X-999")

        assert datos["titulo"] == "Título mínimo"
        assert datos["año"] == 2019
        assert datos["tipo"] == TipoPaper.libro.value
        assert datos["doi"] is None
        assert datos["url_landing"] is None
        assert datos["autores_texto"] is None

    def test_doi_desde_enlace_global(self) -> None:
        html = """<html><body>
        <h1 class="record-title">Paper con DOI en enlace global</h1>
        <p>Más info en <a href="https://doi.org/10.9876/test.paper">este DOI</a></p>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        datos = parsear_detalle(soup, "https://base.example.com", "Y-100")

        assert datos["doi"] == "10.9876/test.paper"


# ---------------------------------------------------------------------------
# parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistro:
    def test_campos_canonicos_presentes(self, harvester: VuFindUATHarvester) -> None:
        raw: dict[str, Any] = {
            "vufind_id": "UAT-001",
            "doi": "10.1234/test",
            "titulo": "Título de prueba",
            "titulo_normalizado": "titulo de prueba",
            "autores_texto": "García, M.",
            "año": 2023,
            "tipo": TipoPaper.articulo.value,
            "revista": "EduCiencia",
            "url_landing": "https://example.com/pdf",
        }
        parsed = harvester.parsear_registro(raw)

        assert parsed["vufind_id"] == "UAT-001"
        assert parsed["fuente_origen"] == TipoFuente.vufind_uat.value
        assert parsed["doi"] == "10.1234/test"
        assert parsed["año"] == 2023

    def test_campos_ausentes_dan_none(self, harvester: VuFindUATHarvester) -> None:
        raw: dict[str, Any] = {
            "titulo": "Solo título",
            "tipo": TipoPaper.otro.value,
        }
        parsed = harvester.parsear_registro(raw)

        assert parsed["vufind_id"] is None
        assert parsed["doi"] is None
        assert parsed["autores_texto"] is None


# ---------------------------------------------------------------------------
# cosechar — flujo completo
# ---------------------------------------------------------------------------


class TestCosechar:
    @pytest.mark.asyncio
    async def test_dos_paginas_tres_registros(self, harvester: VuFindUATHarvester) -> None:
        resp1 = _mk_response(_html("vufind_pagina1.html"))
        resp2 = _mk_response(_html("vufind_pagina2.html"))
        mock_client = _mk_async_client(resp1, resp2)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-abc", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 3
        ids = [r.fuente_id for r in resultados]
        assert "UAT-2022-001" in ids
        assert "UAT-2021-042" in ids
        assert "UAT-2020-007" in ids

    @pytest.mark.asyncio
    async def test_primera_pagina_sin_resultados_para(self, harvester: VuFindUATHarvester) -> None:
        resp = _mk_response(_html("vufind_sin_resultados.html"))
        mock_client = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-xyz", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 0

    @pytest.mark.asyncio
    async def test_error_http_propaga(self, harvester: VuFindUATHarvester) -> None:
        import httpx as _httpx

        resp = _mk_response("", status=503)
        mock_client = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(_httpx.HTTPStatusError),
        ):
            async for _ in harvester.cosechar("cosecha-err", "completa", {}):
                pass

    @pytest.mark.asyncio
    async def test_respeta_max_paginas(self) -> None:
        h = VuFindUATHarvester()
        h.configurar(
            {
                "base_url": "https://publicaciones.uat.edu.mx/vufind",
                "max_paginas_por_corrida": 1,
            }
        )
        # page 1 tiene next, pero max_paginas=1 → debe parar tras la primera
        resp1 = _mk_response(_html("vufind_pagina1.html"))
        mock_client = _mk_async_client(resp1)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in h.cosechar("cosecha-max", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 2  # solo page 1

    @pytest.mark.asyncio
    async def test_cards_sin_vufind_id_se_omiten(self, harvester: VuFindUATHarvester) -> None:
        html = """<html><body>
        <div class="result">
          <div class="media-body">
            <a class="title">Sin href — sin ID</a>
            <div class="format">Artículo</div>
          </div>
        </div>
        </body></html>"""
        resp = _mk_response(html)
        mock_client = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in harvester.cosechar("cosecha-skip", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 0

    @pytest.mark.asyncio
    async def test_cosechar_con_fetch_detalle(self) -> None:
        h = VuFindUATHarvester()
        h.configurar(
            {
                "base_url": "https://publicaciones.uat.edu.mx/vufind",
                "max_paginas_por_corrida": 1,
                "fetch_detalle": True,
            }
        )
        # Pagina 1 (sin siguiente), seguida de 2 detalles (2 cards en página 1)
        resp_lista = _mk_response(_html("vufind_pagina1.html"))
        resp_det1 = _mk_response(_html("vufind_detalle.html"))
        resp_det2 = _mk_response(_html("vufind_detalle.html"))
        mock_client = _mk_async_client(resp_lista, resp_det1, resp_det2)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in h.cosechar("cosecha-det", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 2
        # Los datos del detalle deben haber sobreescrito los de la card
        primer = resultados[0].datos
        assert primer.get("doi") == "10.1234/educiencia.2022.001"

    @pytest.mark.asyncio
    async def test_error_en_detalle_no_aborta_cosecha(self) -> None:
        h = VuFindUATHarvester()
        h.configurar(
            {
                "base_url": "https://publicaciones.uat.edu.mx/vufind",
                "max_paginas_por_corrida": 1,
                "fetch_detalle": True,
            }
        )
        resp_lista = _mk_response(_html("vufind_pagina1.html"))
        resp_det_error = _mk_response("", status=404)
        resp_det_ok = _mk_response(_html("vufind_detalle.html"))
        mock_client = _mk_async_client(resp_lista, resp_det_error, resp_det_ok)

        with (
            patch(
                "intellectclone.harvesters.vufind_uat.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in h.cosechar("cosecha-det-err", "completa", {}):
                resultados.append(r)

        assert len(resultados) == 2  # ambas cards procesadas, error en detalle ignorado


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_health_check_ok(self, harvester: VuFindUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("intellectclone.harvesters.vufind_uat.httpx.get", return_value=resp):
            assert harvester.health_check() is True

    def test_health_check_error_http(self, harvester: VuFindUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 403
        with patch("intellectclone.harvesters.vufind_uat.httpx.get", return_value=resp):
            assert harvester.health_check() is False

    def test_health_check_excepcion_red(self, harvester: VuFindUATHarvester) -> None:
        import httpx as _httpx

        with patch(
            "intellectclone.harvesters.vufind_uat.httpx.get",
            side_effect=_httpx.ConnectError("timeout"),
        ):
            assert harvester.health_check() is False


# ---------------------------------------------------------------------------
# Auto-registro
# ---------------------------------------------------------------------------


class TestAutoRegistro:
    def test_vufind_uat_en_registry(self) -> None:
        import intellectclone.harvesters.vufind_uat  # noqa: F401

        clase = obtener_harvester(TipoFuente.vufind_uat.value)
        assert clase is VuFindUATHarvester

    def test_instancia_es_base_harvester(self) -> None:
        from intellectclone.harvesters.base import BaseHarvester

        assert issubclass(VuFindUATHarvester, BaseHarvester)
