"""
Tests unitarios para CrossrefEnricher (C7).

Cubre:
- _mapear_tipo_crossref: tipos conocidos y desconocido
- _extraer_año_crossref: date-parts completo, solo año, ausente
- _formatear_autores: múltiples autores, sin autores, solo apellido
- parsear_crossref_work: mensaje completo, sin título (→ None), autores varios
- parsear_registro: conversión al formato canónico
- cosechar: DOI vacío → no emite
- cosechar: DOI válido → 1 resultado con metadatos completos
- cosechar: 404 → no emite (DOI no registrado en Crossref)
- cosechar: error HTTP → raise_for_status lanza excepción
- cosechar: fuente_id usa DOI normalizado
- health_check: 200 OK y excepción de red
- auto-registro en registry
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellectclone.harvesters.crossref_enricher import (
    CrossrefEnricher,
    _extraer_año_crossref,
    _formatear_autores,
    _mapear_tipo_crossref,
    parsear_crossref_work,
)
from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "fixtures"
_DOI_TEST = "10.1016/j.nano.2022.42"


def _load_crossref() -> dict[str, Any]:
    return json.loads((_FIXTURES / "crossref_doi.json").read_text())


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
def enricher() -> CrossrefEnricher:
    e = CrossrefEnricher()
    e.configurar({"base_url": "https://api.crossref.test", "mailto": "test@uat.edu.mx"})
    return e


# ---------------------------------------------------------------------------
# Tests: _mapear_tipo_crossref
# ---------------------------------------------------------------------------


class TestMapearTipoCrossref:
    def test_journal_article(self) -> None:
        assert _mapear_tipo_crossref("journal-article") == TipoPaper.articulo.value

    def test_book_chapter(self) -> None:
        assert _mapear_tipo_crossref("book-chapter") == TipoPaper.capitulo.value

    def test_book(self) -> None:
        assert _mapear_tipo_crossref("book") == TipoPaper.libro.value

    def test_proceedings_article(self) -> None:
        assert _mapear_tipo_crossref("proceedings-article") == TipoPaper.memoria_congreso.value

    def test_report(self) -> None:
        assert _mapear_tipo_crossref("report") == TipoPaper.reporte_tecnico.value

    def test_posted_content_preprint(self) -> None:
        assert _mapear_tipo_crossref("posted-content") == TipoPaper.preprint.value

    def test_dissertation(self) -> None:
        assert _mapear_tipo_crossref("dissertation") == TipoPaper.tesis_doctorado.value

    def test_desconocido(self) -> None:
        assert _mapear_tipo_crossref("grant") == TipoPaper.otro.value

    def test_case_insensitive(self) -> None:
        assert _mapear_tipo_crossref("Journal-Article") == TipoPaper.articulo.value


# ---------------------------------------------------------------------------
# Tests: _extraer_año_crossref
# ---------------------------------------------------------------------------


class TestExtraerAñoCrossref:
    def test_fecha_completa(self) -> None:
        published = {"date-parts": [[2022, 3, 10]]}
        assert _extraer_año_crossref(published) == 2022

    def test_solo_año(self) -> None:
        published = {"date-parts": [[2021]]}
        assert _extraer_año_crossref(published) == 2021

    def test_published_none(self) -> None:
        assert _extraer_año_crossref(None) is None

    def test_date_parts_vacio(self) -> None:
        assert _extraer_año_crossref({"date-parts": []}) is None

    def test_date_parts_lista_vacia_interior(self) -> None:
        assert _extraer_año_crossref({"date-parts": [[]]}) is None


# ---------------------------------------------------------------------------
# Tests: _formatear_autores
# ---------------------------------------------------------------------------


class TestFormatearAutores:
    def test_dos_autores(self) -> None:
        authors = [
            {"family": "García López", "given": "Juan"},
            {"family": "Martínez Reyes", "given": "Ana"},
        ]
        result = _formatear_autores(authors)
        assert result == "García López, Juan; Martínez Reyes, Ana"

    def test_autor_sin_given(self) -> None:
        authors = [{"family": "García", "given": ""}]
        result = _formatear_autores(authors)
        assert result == "García"

    def test_lista_vacia(self) -> None:
        assert _formatear_autores([]) is None

    def test_autor_con_solo_given(self) -> None:
        authors = [{"family": "", "given": "Consorcio ABC"}]
        result = _formatear_autores(authors)
        assert result == "Consorcio ABC"


# ---------------------------------------------------------------------------
# Tests: parsear_crossref_work
# ---------------------------------------------------------------------------


class TestParsearCrossrefWork:
    def test_mensaje_completo(self) -> None:
        payload = _load_crossref()
        datos = parsear_crossref_work(payload["message"])
        assert datos is not None
        assert "nanotecnología" in datos["titulo"]
        assert datos["doi"] == "10.1016/j.nano.2022.42"
        assert datos["año"] == 2022
        assert datos["tipo"] == TipoPaper.articulo.value
        assert datos["revista"] == "Nanomaterials"
        assert datos["issn"] == "2079-4991"
        assert datos["editorial"] == "MDPI AG"
        assert datos["autores_texto"] is not None
        assert "García López, Juan" in datos["autores_texto"]  # type: ignore[operator]
        assert datos["fuente_origen"] == TipoFuente.crossref.value

    def test_sin_titulo_retorna_none(self) -> None:
        message: dict[str, Any] = {"DOI": "10.xxx/yyy", "type": "journal-article"}
        assert parsear_crossref_work(message) is None

    def test_titulo_lista_vacia_retorna_none(self) -> None:
        message: dict[str, Any] = {"title": [], "DOI": "10.xxx/yyy"}
        assert parsear_crossref_work(message) is None

    def test_doi_normalizado_minusculas(self) -> None:
        message: dict[str, Any] = {
            "title": ["Test"],
            "DOI": "10.1016/J.NANO.2022.42",
            "type": "journal-article",
        }
        datos = parsear_crossref_work(message)
        assert datos is not None
        assert datos["doi"] == "10.1016/j.nano.2022.42"

    def test_titulo_normalizado_presente(self) -> None:
        payload = _load_crossref()
        datos = parsear_crossref_work(payload["message"])
        assert datos is not None
        assert datos["titulo_normalizado"] is not None

    def test_sin_autores(self) -> None:
        message: dict[str, Any] = {
            "title": ["Paper sin autores"],
            "DOI": "10.xxx/yyy",
            "type": "report",
        }
        datos = parsear_crossref_work(message)
        assert datos is not None
        assert datos["autores_texto"] is None

    def test_published_print_fallback(self) -> None:
        """Si 'published' no existe, usa 'published-print'."""
        message: dict[str, Any] = {
            "title": ["Test"],
            "DOI": "10.xxx/yyy",
            "type": "journal-article",
            "published-print": {"date-parts": [[2019, 5]]},
        }
        datos = parsear_crossref_work(message)
        assert datos is not None
        assert datos["año"] == 2019


# ---------------------------------------------------------------------------
# Tests: parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistro:
    def test_formato_canonico(self, enricher: CrossrefEnricher) -> None:
        raw: dict[str, Any] = {
            "doi": "10.1016/j.nano.2022.42",
            "titulo": "Título",
            "titulo_normalizado": "titulo",
            "autores_texto": "García, Juan",
            "año": 2022,
            "tipo": TipoPaper.articulo.value,
            "revista": "Nano",
            "issn": "2079-4991",
            "editorial": "MDPI AG",
        }
        parsed = enricher.parsear_registro(raw)
        assert parsed["fuente_origen"] == TipoFuente.crossref.value
        assert parsed["doi"] == "10.1016/j.nano.2022.42"
        assert parsed["issn"] == "2079-4991"
        assert parsed["editorial"] == "MDPI AG"

    def test_tipo_default_otro(self, enricher: CrossrefEnricher) -> None:
        parsed = enricher.parsear_registro({"titulo": "X"})
        assert parsed["tipo"] == TipoPaper.otro.value


# ---------------------------------------------------------------------------
# Tests: cosechar
# ---------------------------------------------------------------------------


class TestCosechar:
    @pytest.mark.asyncio
    async def test_doi_vacio_no_emite(self, enricher: CrossrefEnricher) -> None:
        with patch("intellectclone.harvesters.crossref_enricher.httpx.AsyncClient"):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c1", "enriquecimiento", {}):
                resultados.append(r)
        assert resultados == []

    @pytest.mark.asyncio
    async def test_doi_valido_emite_un_resultado(self, enricher: CrossrefEnricher) -> None:
        payload = _load_crossref()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.crossref_enricher.asyncio.sleep", new_callable=AsyncMock
            ),
            patch(
                "intellectclone.harvesters.crossref_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c2", "enriquecimiento", {"doi": _DOI_TEST}):
                resultados.append(r)

        assert len(resultados) == 1
        assert resultados[0].datos["doi"] == _DOI_TEST

    @pytest.mark.asyncio
    async def test_404_no_emite(self, enricher: CrossrefEnricher) -> None:
        resp = _mk_response({}, status_code=404)
        client_mock = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.crossref_enricher.asyncio.sleep", new_callable=AsyncMock
            ),
            patch(
                "intellectclone.harvesters.crossref_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c3", "enriquecimiento", {"doi": _DOI_TEST}):
                resultados.append(r)

        assert resultados == []

    @pytest.mark.asyncio
    async def test_500_propaga_excepcion(self, enricher: CrossrefEnricher) -> None:
        import httpx

        resp = _mk_response({}, status_code=500)
        client_mock = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.crossref_enricher.asyncio.sleep", new_callable=AsyncMock
            ),
            patch(
                "intellectclone.harvesters.crossref_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
            pytest.raises(httpx.HTTPStatusError),
        ):
            async for _ in enricher.cosechar("c4", "enriquecimiento", {"doi": _DOI_TEST}):
                pass

    @pytest.mark.asyncio
    async def test_fuente_id_usa_doi_normalizado(self, enricher: CrossrefEnricher) -> None:
        payload = _load_crossref()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.crossref_enricher.asyncio.sleep", new_callable=AsyncMock
            ),
            patch(
                "intellectclone.harvesters.crossref_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c5", "enriquecimiento", {"doi": _DOI_TEST}):
                resultados.append(r)

        assert resultados[0].fuente_id == _DOI_TEST

    @pytest.mark.asyncio
    async def test_metadatos_completos_en_resultado(self, enricher: CrossrefEnricher) -> None:
        payload = _load_crossref()
        resp = _mk_response(payload)
        client_mock = _mk_async_client(resp)

        with (
            patch(
                "intellectclone.harvesters.crossref_enricher.asyncio.sleep", new_callable=AsyncMock
            ),
            patch(
                "intellectclone.harvesters.crossref_enricher.httpx.AsyncClient",
                return_value=client_mock,
            ),
        ):
            resultados: list[ResultadoCosecha] = []
            async for r in enricher.cosechar("c6", "enriquecimiento", {"doi": _DOI_TEST}):
                resultados.append(r)

        datos = resultados[0].datos
        assert datos["año"] == 2022
        assert datos["editorial"] == "MDPI AG"
        assert datos["issn"] == "2079-4991"
        assert datos["revista"] == "Nanomaterials"
        assert datos["autores_texto"] is not None


# ---------------------------------------------------------------------------
# Tests: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_retorna_true_con_200(self, enricher: CrossrefEnricher) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("intellectclone.harvesters.crossref_enricher.httpx.get", return_value=resp):
            assert enricher.health_check() is True

    def test_retorna_false_con_404(self, enricher: CrossrefEnricher) -> None:
        resp = MagicMock()
        resp.status_code = 404
        with patch("intellectclone.harvesters.crossref_enricher.httpx.get", return_value=resp):
            assert enricher.health_check() is False

    def test_retorna_false_en_excepcion(self, enricher: CrossrefEnricher) -> None:
        import httpx

        with patch(
            "intellectclone.harvesters.crossref_enricher.httpx.get",
            side_effect=httpx.ConnectError("err"),
        ):
            assert enricher.health_check() is False


# ---------------------------------------------------------------------------
# Tests: auto-registro
# ---------------------------------------------------------------------------


class TestAutoRegistro:
    def test_crossref_registrado_en_registry(self) -> None:
        import intellectclone.harvesters.crossref_enricher  # noqa: F401

        harvester_cls = obtener_harvester(TipoFuente.crossref.value)
        assert harvester_cls is CrossrefEnricher

    def test_fuente_tipo(self) -> None:
        assert CrossrefEnricher.fuente_tipo == TipoFuente.crossref.value
