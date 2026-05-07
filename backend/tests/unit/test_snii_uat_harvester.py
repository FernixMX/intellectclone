"""
Tests unitarios para SNIIUATHarvester (C8).

Cubre:
- detectar_captcha: página con captcha y sin captcha
- detectar_tabla: tabla presente, ausente, tabla buscador
- parsear_tabla_campus_ca: 3 registros, graduaciones, sin tabla
- parsear_tabla_campus_ca: fixture paginado (1 registro)
- parsear_tabla_buscador: 3 investigadores, nivel_snii, vigencia, ca vacío
- extraer_pagina_siguiente: hay siguiente, no hay, fuera de rango
- parsear_registro: pass-through canónico
- cosechar campus_ca: modo campus_ca con 1 campus → 3 resultados
- cosechar buscador_snii: modo buscador con 1 dependencia → 3 resultados
- cosechar completo: ambos modos combinados
- cosechar captcha inicial: _AntiScrapingError en campus_ca
- cosechar captcha en resultado: _AntiScrapingError al filtrar
- cosechar sin tabla: opción sin resultados se salta correctamente
- health_check: 200 OK y excepción de red
- configurar: override de base_url
- auto-registro en registry
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.snii_uat import (
    SNIIUATHarvester,
    _AntiScrapingError,
    detectar_captcha,
    detectar_tabla,
    extraer_pagina_siguiente,
    parsear_tabla_buscador,
    parsear_tabla_campus_ca,
)
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import NivelSnii, TipoFuente

# ---------------------------------------------------------------------------
# Rutas de fixtures
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "fixtures"

_HTML_CAMPUS_CA = (_FIXTURES / "snii_campus_ca.html").read_text()
_HTML_PAGINADA = (_FIXTURES / "snii_campus_ca_paginada.html").read_text()
_HTML_BUSCADOR = (_FIXTURES / "snii_buscador.html").read_text()
_HTML_CAPTCHA = (_FIXTURES / "snii_captcha.html").read_text()
_HTML_SIN_TABLA = (_FIXTURES / "snii_sin_tabla.html").read_text()

# ---------------------------------------------------------------------------
# Helpers de mock de Playwright
# ---------------------------------------------------------------------------


def _mk_page(content_side_effects: list[str], options: list[dict[str, str]]) -> MagicMock:
    page = MagicMock()
    page.goto = AsyncMock()
    page.content = AsyncMock(side_effect=content_side_effects)
    page.eval_on_selector_all = AsyncMock(return_value=options)
    page.select_option = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.evaluate = AsyncMock(return_value=False)
    page.close = AsyncMock()
    return page


def _mk_playwright(page: MagicMock) -> MagicMock:
    browser = MagicMock()
    browser.new_page = AsyncMock(return_value=page)
    browser.close = AsyncMock()

    pw = MagicMock()
    pw.chromium = MagicMock()
    pw.chromium.launch = AsyncMock(return_value=browser)
    pw.__aenter__ = AsyncMock(return_value=pw)
    pw.__aexit__ = AsyncMock(return_value=False)

    return pw


# ---------------------------------------------------------------------------
# Fixture de harvester configurado
# ---------------------------------------------------------------------------


@pytest.fixture()
def harvester() -> SNIIUATHarvester:
    h = SNIIUATHarvester()
    h.configurar({"base_url": "https://produccioncientifica.test"})
    return h


# ---------------------------------------------------------------------------
# Tests: detectar_captcha
# ---------------------------------------------------------------------------


class TestDetectarCaptcha:
    def test_detecta_recaptcha_div(self) -> None:
        assert detectar_captcha(_HTML_CAPTCHA) is True

    def test_detecta_challenge_container(self) -> None:
        html = "<div id='challenge-container'>verifica</div>"
        assert detectar_captcha(html) is True

    def test_detecta_img_captcha(self) -> None:
        html = "<img src='/captcha.png' />"
        assert detectar_captcha(html) is True

    def test_no_captcha_campus_ca(self) -> None:
        assert detectar_captcha(_HTML_CAMPUS_CA) is False

    def test_no_captcha_buscador(self) -> None:
        assert detectar_captcha(_HTML_BUSCADOR) is False

    def test_no_captcha_sin_tabla(self) -> None:
        assert detectar_captcha(_HTML_SIN_TABLA) is False


# ---------------------------------------------------------------------------
# Tests: detectar_tabla
# ---------------------------------------------------------------------------


class TestDetectarTabla:
    def test_tabla_campus_ca_presente(self) -> None:
        assert detectar_tabla(_HTML_CAMPUS_CA, "ContentPlaceHolder1_GridView1") is True

    def test_tabla_campus_ca_ausente_sin_tabla(self) -> None:
        assert detectar_tabla(_HTML_SIN_TABLA, "ContentPlaceHolder1_GridView1") is False

    def test_tabla_buscador_presente(self) -> None:
        assert detectar_tabla(_HTML_BUSCADOR, "ContentPlaceHolder1_GridViewInvestigadores") is True

    def test_tabla_buscador_ausente_en_campus(self) -> None:
        assert (
            detectar_tabla(_HTML_CAMPUS_CA, "ContentPlaceHolder1_GridViewInvestigadores") is False
        )

    def test_tabla_paginada_presente(self) -> None:
        assert detectar_tabla(_HTML_PAGINADA, "ContentPlaceHolder1_GridView1") is True


# ---------------------------------------------------------------------------
# Tests: parsear_tabla_campus_ca
# ---------------------------------------------------------------------------


class TestParsearTablaCampusCa:
    def test_tres_registros(self) -> None:
        regs = parsear_tabla_campus_ca(_HTML_CAMPUS_CA)
        assert len(regs) == 3

    def test_primer_registro_completo(self) -> None:
        reg = parsear_tabla_campus_ca(_HTML_CAMPUS_CA)[0]
        assert reg["nombre_ca"] == "Biotecnología Agropecuaria"
        assert reg["campus"] == "Cd. Victoria"
        assert reg["clave_ca"] == "UAT-CA-001"
        assert reg["grado_consolidacion"] == "consolidado"
        assert reg["area_conocimiento"] == "Ciencias Agropecuarias y Biotecnología"
        assert reg["responsable"] == "García López, Juan"

    def test_segundo_registro_grado_en_consolidacion(self) -> None:
        reg = parsear_tabla_campus_ca(_HTML_CAMPUS_CA)[1]
        assert reg["nombre_ca"] == "Matemáticas Aplicadas y Cómputo"
        assert reg["grado_consolidacion"] == "en_consolidacion"

    def test_tercer_registro_grado_en_formacion(self) -> None:
        reg = parsear_tabla_campus_ca(_HTML_CAMPUS_CA)[2]
        assert reg["nombre_ca"] == "Nanomateriales y Energía Sustentable"
        assert reg["grado_consolidacion"] == "en_formacion"

    def test_tipo_registro_es_cuerpo_academico(self) -> None:
        for reg in parsear_tabla_campus_ca(_HTML_CAMPUS_CA):
            assert reg["tipo_registro"] == "cuerpo_academico"

    def test_fuente_origen_snii_uat(self) -> None:
        for reg in parsear_tabla_campus_ca(_HTML_CAMPUS_CA):
            assert reg["fuente_origen"] == TipoFuente.snii_uat.value

    def test_sin_tabla_devuelve_lista_vacia(self) -> None:
        assert parsear_tabla_campus_ca(_HTML_SIN_TABLA) == []

    def test_captcha_devuelve_lista_vacia(self) -> None:
        assert parsear_tabla_campus_ca(_HTML_CAPTCHA) == []

    def test_paginada_un_registro(self) -> None:
        regs = parsear_tabla_campus_ca(_HTML_PAGINADA)
        assert len(regs) == 1
        assert regs[0]["nombre_ca"] == "Ingeniería Computacional"
        assert regs[0]["clave_ca"] == "UAT-CA-045"


# ---------------------------------------------------------------------------
# Tests: parsear_tabla_buscador
# ---------------------------------------------------------------------------


class TestParsearTablaBuscador:
    def test_tres_investigadores(self) -> None:
        regs = parsear_tabla_buscador(_HTML_BUSCADOR)
        assert len(regs) == 3

    def test_primer_investigador_nivel_i(self) -> None:
        reg = parsear_tabla_buscador(_HTML_BUSCADOR)[0]
        assert reg["nombre_completo"] == "García López, Juan"
        assert reg["campus"] == "Cd. Victoria"
        assert reg["nombre_ca"] == "Biotecnología Agropecuaria"
        assert reg["nivel_snii"] == NivelSnii.nivel_1.value
        assert reg["vigencia_snii"] == 2025

    def test_segundo_investigador_candidato(self) -> None:
        reg = parsear_tabla_buscador(_HTML_BUSCADOR)[1]
        assert reg["nombre_completo"] == "Martínez Reyes, Ana"
        assert reg["nivel_snii"] == NivelSnii.candidato.value
        assert reg["vigencia_snii"] == 2024

    def test_tercer_investigador_nivel_ii(self) -> None:
        reg = parsear_tabla_buscador(_HTML_BUSCADOR)[2]
        assert reg["nombre_completo"] == "López Hernández, María"
        assert reg["nivel_snii"] == NivelSnii.nivel_2.value
        assert reg["vigencia_snii"] == 2026

    def test_nombre_ca_vacio_es_none(self) -> None:
        reg = parsear_tabla_buscador(_HTML_BUSCADOR)[2]
        assert reg["nombre_ca"] is None

    def test_tipo_registro_es_investigador_snii(self) -> None:
        for reg in parsear_tabla_buscador(_HTML_BUSCADOR):
            assert reg["tipo_registro"] == "investigador_snii"

    def test_fuente_origen_snii_uat(self) -> None:
        for reg in parsear_tabla_buscador(_HTML_BUSCADOR):
            assert reg["fuente_origen"] == TipoFuente.snii_uat.value

    def test_sin_tabla_devuelve_lista_vacia(self) -> None:
        assert parsear_tabla_buscador(_HTML_SIN_TABLA) == []


# ---------------------------------------------------------------------------
# Tests: extraer_pagina_siguiente
# ---------------------------------------------------------------------------


class TestExtraerPaginaSiguiente:
    def test_pagina_2_existe(self) -> None:
        assert extraer_pagina_siguiente(_HTML_PAGINADA, 1) == 2

    def test_no_hay_siguiente_en_campus_ca(self) -> None:
        assert extraer_pagina_siguiente(_HTML_CAMPUS_CA, 1) is None

    def test_pagina_3_no_existe_en_fixture(self) -> None:
        assert extraer_pagina_siguiente(_HTML_PAGINADA, 2) is None

    def test_sin_tabla_no_hay_paginacion(self) -> None:
        assert extraer_pagina_siguiente(_HTML_SIN_TABLA, 1) is None


# ---------------------------------------------------------------------------
# Tests: parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistro:
    def test_pass_through_cuerpo_academico(self, harvester: SNIIUATHarvester) -> None:
        raw: dict[str, Any] = {
            "tipo_registro": "cuerpo_academico",
            "campus": "Tampico",
            "nombre_ca": "Test CA",
            "clave_ca": "UAT-CA-999",
            "grado_consolidacion": "consolidado",
            "area_conocimiento": "Ingeniería",
            "responsable": "Fulano",
            "fuente_origen": TipoFuente.snii_uat.value,
        }
        result = harvester.parsear_registro(raw)
        assert result == raw

    def test_pass_through_investigador(self, harvester: SNIIUATHarvester) -> None:
        raw: dict[str, Any] = {
            "tipo_registro": "investigador_snii",
            "nombre_completo": "Fulano De Tal",
            "nivel_snii": NivelSnii.nivel_1.value,
            "vigencia_snii": 2025,
            "fuente_origen": TipoFuente.snii_uat.value,
        }
        result = harvester.parsear_registro(raw)
        assert result == raw


# ---------------------------------------------------------------------------
# Tests: cosechar campus_ca (Playwright mockeado)
# ---------------------------------------------------------------------------


class TestCosecharCampusCa:
    async def test_tres_resultados_campus_victoria(self, harvester: SNIIUATHarvester) -> None:
        opciones = [
            {"value": "", "text": "-- Todos --"},
            {"value": "victoria", "text": "Cd. Victoria"},
        ]
        page = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA, _HTML_CAMPUS_CA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("c001", "campus_ca", {}):
                resultados.append(r)

        assert len(resultados) == 3
        assert all(r.datos["tipo_registro"] == "cuerpo_academico" for r in resultados)

    async def test_opcion_vacia_se_salta(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "", "text": "-- Todos --"}]
        page = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("c002", "campus_ca", {}):
                resultados.append(r)

        assert len(resultados) == 0

    async def test_sin_tabla_se_salta_campus(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "reynosa", "text": "Reynosa"}]
        page = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA, _HTML_SIN_TABLA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("c003", "campus_ca", {}):
                resultados.append(r)

        assert len(resultados) == 0

    async def test_captcha_inicial_lanza_error(self, harvester: SNIIUATHarvester) -> None:
        opciones: list[dict[str, str]] = []
        page = _mk_page(
            content_side_effects=[_HTML_CAPTCHA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(_AntiScrapingError, match="CampusCA.aspx"),
        ):
            async for _ in harvester.cosechar("c004", "campus_ca", {}):
                pass

    async def test_captcha_en_resultado_lanza_error(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "victoria", "text": "Cd. Victoria"}]
        page = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA, _HTML_CAPTCHA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(_AntiScrapingError, match="victoria"),
        ):
            async for _ in harvester.cosechar("c005", "campus_ca", {}):
                pass

    async def test_resultados_tienen_fuente_id(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "victoria", "text": "Cd. Victoria"}]
        page = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA, _HTML_CAMPUS_CA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("c006", "campus_ca", {}):
                resultados.append(r)

        for r in resultados:
            assert r.fuente_id  # no vacío


# ---------------------------------------------------------------------------
# Tests: cosechar buscador_snii (Playwright mockeado)
# ---------------------------------------------------------------------------


class TestCosecharBuscador:
    async def test_tres_resultados_dependencia(self, harvester: SNIIUATHarvester) -> None:
        opciones = [
            {"value": "", "text": "-- Todas --"},
            {"value": "FCAT", "text": "Fac. Ciencias Agropecuarias y Tecnología"},
        ]
        page = _mk_page(
            content_side_effects=[_HTML_BUSCADOR, _HTML_BUSCADOR],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("b001", "buscador_snii", {}):
                resultados.append(r)

        assert len(resultados) == 3
        assert all(r.datos["tipo_registro"] == "investigador_snii" for r in resultados)

    async def test_captcha_inicial_lanza_error(self, harvester: SNIIUATHarvester) -> None:
        opciones: list[dict[str, str]] = []
        page = _mk_page(
            content_side_effects=[_HTML_CAPTCHA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(_AntiScrapingError, match="Buscador.aspx"),
        ):
            async for _ in harvester.cosechar("b002", "buscador_snii", {}):
                pass

    async def test_sin_tabla_se_salta_dependencia(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "FMEDIC", "text": "Fac. de Medicina"}]
        page = _mk_page(
            content_side_effects=[_HTML_BUSCADOR, _HTML_SIN_TABLA],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("b003", "buscador_snii", {}):
                resultados.append(r)

        assert len(resultados) == 0

    async def test_fuente_id_es_nombre_completo(self, harvester: SNIIUATHarvester) -> None:
        opciones = [{"value": "FCAT", "text": "FCAT"}]
        page = _mk_page(
            content_side_effects=[_HTML_BUSCADOR, _HTML_BUSCADOR],
            options=opciones,
        )
        pw = _mk_playwright(page)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("b004", "buscador_snii", {}):
                resultados.append(r)

        nombres = {r.fuente_id for r in resultados}
        assert "García López, Juan" in nombres


# ---------------------------------------------------------------------------
# Tests: cosechar modo completo
# ---------------------------------------------------------------------------


class TestCosecharCompleto:
    async def test_modo_completo_combina_ambos(self, harvester: SNIIUATHarvester) -> None:
        opciones_ca = [{"value": "victoria", "text": "Cd. Victoria"}]
        opciones_buscador = [{"value": "FCAT", "text": "FCAT"}]

        page_ca = _mk_page(
            content_side_effects=[_HTML_CAMPUS_CA, _HTML_CAMPUS_CA],
            options=opciones_ca,
        )
        page_buscador = _mk_page(
            content_side_effects=[_HTML_BUSCADOR, _HTML_BUSCADOR],
            options=opciones_buscador,
        )

        browser = MagicMock()
        browser.new_page = AsyncMock(side_effect=[page_ca, page_buscador])
        browser.close = AsyncMock()

        pw = MagicMock()
        pw.chromium = MagicMock()
        pw.chromium.launch = AsyncMock(return_value=browser)
        pw.__aenter__ = AsyncMock(return_value=pw)
        pw.__aexit__ = AsyncMock(return_value=False)

        resultados: list[ResultadoCosecha] = []
        with (
            patch("intellectclone.harvesters.snii_uat.async_playwright", return_value=pw),
            patch("intellectclone.harvesters.snii_uat.asyncio.sleep", new_callable=AsyncMock),
        ):
            async for r in harvester.cosechar("x001", "completo", {}):
                resultados.append(r)

        tipos = {r.datos["tipo_registro"] for r in resultados}
        assert "cuerpo_academico" in tipos
        assert "investigador_snii" in tipos
        assert len(resultados) == 6


# ---------------------------------------------------------------------------
# Tests: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_health_ok(self, harvester: SNIIUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("intellectclone.harvesters.snii_uat.httpx.get", return_value=resp):
            assert harvester.health_check() is True

    def test_health_error_status(self, harvester: SNIIUATHarvester) -> None:
        resp = MagicMock()
        resp.status_code = 403
        with patch("intellectclone.harvesters.snii_uat.httpx.get", return_value=resp):
            assert harvester.health_check() is False

    def test_health_excepcion_red(self, harvester: SNIIUATHarvester) -> None:
        with patch(
            "intellectclone.harvesters.snii_uat.httpx.get",
            side_effect=httpx.ConnectError("sin red"),
        ):
            assert harvester.health_check() is False


# ---------------------------------------------------------------------------
# Tests: configurar
# ---------------------------------------------------------------------------


class TestConfigurar:
    def test_base_url_override(self) -> None:
        h = SNIIUATHarvester()
        h.configurar({"base_url": "https://mi.servidor.edu.mx/"})
        assert h._base_url == "https://mi.servidor.edu.mx"

    def test_timeout_ms_override(self) -> None:
        h = SNIIUATHarvester()
        h.configurar({"timeout_ms": 60_000})
        assert h._timeout_ms == 60_000

    def test_defaults(self) -> None:
        h = SNIIUATHarvester()
        h.configurar({})
        assert "produccioncientifica.uat.edu.mx" in h._base_url
        assert h._timeout_ms == 30_000


# ---------------------------------------------------------------------------
# Tests: auto-registro
# ---------------------------------------------------------------------------


class TestAutoRegistro:
    def test_snii_uat_registrado(self) -> None:
        cls = obtener_harvester(TipoFuente.snii_uat.value)
        assert cls is SNIIUATHarvester

    def test_fuente_tipo_correcto(self) -> None:
        assert SNIIUATHarvester.fuente_tipo == TipoFuente.snii_uat.value

    def test_nombre_harvester(self) -> None:
        assert SNIIUATHarvester.nombre == "SNII-UAT"
