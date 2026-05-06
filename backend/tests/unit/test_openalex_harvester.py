"""
Tests unitarios para OpenAlexHarvester (C3).

Cubre:
- reconstruir_abstract (pura)
- _mapear_tipo (pura)
- parsear_registro con work completo y work mínimo
- _construir_filtro para cada modo
- cosechar con httpx mockeado: página única, paginación cursor, límite max_works
- health_check
- auto-registro en el registry
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellectclone.harvesters.openalex import (
    OpenAlexHarvester,
    _extraer_openalex_id,
    _mapear_tipo,
    _ror_sin_prefijo,
    reconstruir_abstract,
)
from intellectclone.harvesters.runner import obtener_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper
from tests.fixtures.openalex_work import (
    PAGE_1_RESPONSE,
    PAGE_2_RESPONSE,
    WORK_COMPLETO,
    WORK_MINIMO,
)

# ---------------------------------------------------------------------------
# Fixture harvester configurado
# ---------------------------------------------------------------------------


@pytest.fixture()
def harvester() -> OpenAlexHarvester:
    h = OpenAlexHarvester()
    h.configurar(
        {
            "polite_pool_email": "test@uat.edu.mx",
            "ror_id_uat": "https://ror.org/00qm7vk32",
            "max_works_por_corrida": 100,
        }
    )
    return h


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------


class TestReconstruirAbstract:
    def test_orden_correcto(self) -> None:
        inv = {"Hola": [0], "mundo": [1]}
        assert reconstruir_abstract(inv) == "Hola mundo"

    def test_posiciones_dispersas(self) -> None:
        inv = {"B": [1], "A": [0], "C": [2]}
        assert reconstruir_abstract(inv) == "A B C"

    def test_palabra_repetida_dos_posiciones(self) -> None:
        inv = {"el": [0, 3], "perro": [1], "persigue": [2]}
        assert reconstruir_abstract(inv) == "el perro persigue el"

    def test_vacio(self) -> None:
        assert reconstruir_abstract({}) == ""

    def test_ejemplo_fixture(self) -> None:
        inv = WORK_COMPLETO["abstract_inverted_index"]
        abstract = reconstruir_abstract(inv)
        assert "redes" in abstract
        assert "neuronales" in abstract
        assert abstract.startswith("Las")

    def test_none_devuelve_vacio(self) -> None:
        assert reconstruir_abstract(None) == ""  # type: ignore[arg-type]


class TestMapearTipo:
    def test_journal_article(self) -> None:
        assert _mapear_tipo("journal-article") == TipoPaper.articulo.value

    def test_article(self) -> None:
        assert _mapear_tipo("article") == TipoPaper.articulo.value

    def test_book_chapter(self) -> None:
        assert _mapear_tipo("book-chapter") == TipoPaper.capitulo.value

    def test_book(self) -> None:
        assert _mapear_tipo("book") == TipoPaper.libro.value

    def test_dissertation(self) -> None:
        assert _mapear_tipo("dissertation") == TipoPaper.tesis_doctorado.value

    def test_proceedings(self) -> None:
        assert _mapear_tipo("proceedings-article") == TipoPaper.memoria_congreso.value

    def test_report(self) -> None:
        assert _mapear_tipo("report") == TipoPaper.reporte_tecnico.value

    def test_preprint(self) -> None:
        assert _mapear_tipo("preprint") == TipoPaper.preprint.value

    def test_desconocido(self) -> None:
        assert _mapear_tipo("unknown-type") == TipoPaper.otro.value

    def test_vacio(self) -> None:
        assert _mapear_tipo("") == TipoPaper.otro.value

    def test_mayusculas(self) -> None:
        assert _mapear_tipo("Journal-Article") == TipoPaper.articulo.value


class TestExtractores:
    def test_extraer_openalex_id(self) -> None:
        assert _extraer_openalex_id("https://openalex.org/W2741809807") == "W2741809807"

    def test_extraer_openalex_id_vacio(self) -> None:
        assert _extraer_openalex_id("") == ""

    def test_ror_sin_prefijo(self) -> None:
        assert _ror_sin_prefijo("https://ror.org/00qm7vk32") == "00qm7vk32"

    def test_ror_ya_limpio(self) -> None:
        assert _ror_sin_prefijo("00qm7vk32") == "00qm7vk32"


# ---------------------------------------------------------------------------
# parsear_registro
# ---------------------------------------------------------------------------


class TestParsearRegistroCompleto:
    def test_openalex_id(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["openalex_id"] == "W2741809807"

    def test_doi_normalizado(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["doi"] == "10.1016/j.neunet.2020.01.001"
        assert "https://" not in parsed["doi"]

    def test_titulo(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["titulo"] == "Redes Neuronales Artificiales: Una Revisión"

    def test_titulo_normalizado_sin_puntuacion(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        titulo_norm = parsed["titulo_normalizado"]
        assert titulo_norm is not None
        assert ":" not in titulo_norm
        assert titulo_norm == titulo_norm.lower()

    def test_abstract_reconstruido(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["abstract_texto"] is not None
        assert "redes" in parsed["abstract_texto"]

    def test_año(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["año"] == 2020

    def test_fecha_publicacion(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["fecha_publicacion"] == "2020-03-15"

    def test_idioma(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["idioma"] == "es"

    def test_revista(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["revista"] == "Neural Networks"

    def test_issn(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["issn"] == "0893-6080"

    def test_volumen_numero_paginas(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["volumen"] == "125"
        assert parsed["numero"] == "3"
        assert parsed["paginas"] == "100-115"

    def test_open_access(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["open_access"] is True

    def test_urls(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["url_pdf"] == "https://example.com/paper.pdf"
        assert "doi.org" in parsed["url_landing"]

    def test_citas(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["total_citas"] == 42
        assert parsed["citas_por_año"] == {"2020": 5, "2021": 15, "2022": 22}

    def test_conceptos(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["conceptos"] is not None
        assert "Artificial neural network" in parsed["conceptos"]

    def test_tipo(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["tipo"] == TipoPaper.articulo.value

    def test_fuente_origen(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert parsed["fuente_origen"] == TipoFuente.openalex.value

    def test_autorships_preservados(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_COMPLETO)
        assert len(parsed["autorships"]) == 2
        assert parsed["autorships"][0]["author"]["display_name"] == "María Elena Cárdenas Ruiz"


class TestParsearRegistroMinimo:
    def test_doi_none(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["doi"] is None

    def test_abstract_none_cuando_no_hay_inverted_index(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["abstract_texto"] is None

    def test_tipo_desconocido_mapea_a_otro(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["tipo"] == TipoPaper.otro.value

    def test_citas_por_año_none_cuando_vacio(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["citas_por_año"] is None

    def test_conceptos_none_cuando_vacio(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["conceptos"] is None

    def test_open_access_false_cuando_none(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["open_access"] is False

    def test_paginas_none_sin_biblio(self, harvester: OpenAlexHarvester) -> None:
        parsed = harvester.parsear_registro(WORK_MINIMO)
        assert parsed["paginas"] is None


# ---------------------------------------------------------------------------
# _construir_filtro
# ---------------------------------------------------------------------------


class TestConstruirFiltro:
    def test_completa(self, harvester: OpenAlexHarvester) -> None:
        f = harvester._construir_filtro("completa", {})
        assert "institutions.ror:00qm7vk32" in f

    def test_incremental(self, harvester: OpenAlexHarvester) -> None:
        f = harvester._construir_filtro("incremental", {"desde_fecha": "2025-01-01"})
        assert "from_publication_date:2025-01-01" in f
        assert "institutions.ror:00qm7vk32" in f

    def test_persona_individual(self, harvester: OpenAlexHarvester) -> None:
        f = harvester._construir_filtro("persona_individual", {"author_id": "A123"})
        assert f == "author.id:A123"

    def test_modo_desconocido_usa_ror(self, harvester: OpenAlexHarvester) -> None:
        f = harvester._construir_filtro("desconocido", {})
        assert "institutions.ror:00qm7vk32" in f


# ---------------------------------------------------------------------------
# cosechar (async, httpx mockeado)
# ---------------------------------------------------------------------------


def _mk_response(data: dict[str, Any], status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    if status >= 400:
        import httpx as _httpx

        resp.raise_for_status.side_effect = _httpx.HTTPStatusError(
            f"HTTP {status}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _mk_async_client(*responses: MagicMock) -> MagicMock:
    """Crea un mock de httpx.AsyncClient que devuelve las respuestas en orden."""
    client = AsyncMock()
    client.get = AsyncMock(side_effect=list(responses))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
async def test_cosechar_pagina_unica(harvester: OpenAlexHarvester) -> None:
    pagina = {
        "meta": {"count": 1, "per_page": 200, "cursor": "*", "next_cursor": None},
        "results": [WORK_COMPLETO],
    }
    mock_client = _mk_async_client(_mk_response(pagina))

    with patch("intellectclone.harvesters.openalex.httpx.AsyncClient", return_value=mock_client):
        resultados: list[ResultadoCosecha] = []
        async for r in harvester.cosechar("c-001", "completa", {}):
            resultados.append(r)

    assert len(resultados) == 1
    assert resultados[0].fuente_id == "W2741809807"
    assert resultados[0].datos["tipo"] == TipoPaper.articulo.value


@pytest.mark.asyncio
async def test_cosechar_paginacion_cursor(harvester: OpenAlexHarvester) -> None:
    mock_client = _mk_async_client(
        _mk_response(PAGE_1_RESPONSE),
        _mk_response(PAGE_2_RESPONSE),
    )

    with patch("intellectclone.harvesters.openalex.httpx.AsyncClient", return_value=mock_client):
        resultados: list[ResultadoCosecha] = []
        async for r in harvester.cosechar("c-002", "completa", {}):
            resultados.append(r)

    assert len(resultados) == 3
    ids = [r.fuente_id for r in resultados]
    assert "W2741809807" in ids
    assert "W9999999999" in ids
    assert "W1111111111" in ids


@pytest.mark.asyncio
async def test_cosechar_respeta_max_works(harvester: OpenAlexHarvester) -> None:
    harvester._max_works = 1
    pagina = {
        "meta": {"count": 100, "per_page": 200, "cursor": "*", "next_cursor": "cursor_2"},
        "results": [WORK_COMPLETO, WORK_MINIMO],
    }
    mock_client = _mk_async_client(_mk_response(pagina))

    with patch("intellectclone.harvesters.openalex.httpx.AsyncClient", return_value=mock_client):
        resultados: list[ResultadoCosecha] = []
        async for r in harvester.cosechar("c-003", "completa", {}):
            resultados.append(r)

    assert len(resultados) == 1


@pytest.mark.asyncio
async def test_cosechar_resultados_vacios(harvester: OpenAlexHarvester) -> None:
    pagina: dict[str, Any] = {
        "meta": {"count": 0, "per_page": 200, "cursor": "*", "next_cursor": None},
        "results": [],
    }
    mock_client = _mk_async_client(_mk_response(pagina))

    with patch("intellectclone.harvesters.openalex.httpx.AsyncClient", return_value=mock_client):
        resultados: list[ResultadoCosecha] = []
        async for r in harvester.cosechar("c-004", "completa", {}):
            resultados.append(r)

    assert resultados == []


@pytest.mark.asyncio
async def test_cosechar_propaga_error_http(harvester: OpenAlexHarvester) -> None:
    mock_client = _mk_async_client(_mk_response({}, status=429))

    import httpx as _httpx

    with (
        patch("intellectclone.harvesters.openalex.httpx.AsyncClient", return_value=mock_client),
        pytest.raises(_httpx.HTTPStatusError),
    ):
        async for _ in harvester.cosechar("c-005", "completa", {}):
            pass


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


def test_health_check_ok(harvester: OpenAlexHarvester) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("intellectclone.harvesters.openalex.httpx.get", return_value=mock_resp):
        assert harvester.health_check() is True


def test_health_check_error(harvester: OpenAlexHarvester) -> None:
    with patch("intellectclone.harvesters.openalex.httpx.get", side_effect=Exception("timeout")):
        assert harvester.health_check() is False


# ---------------------------------------------------------------------------
# Auto-registro
# ---------------------------------------------------------------------------


def test_auto_registro_en_registry() -> None:
    clase = obtener_harvester(TipoFuente.openalex.value)
    assert clase is OpenAlexHarvester


# ---------------------------------------------------------------------------
# Integración normalizer
# ---------------------------------------------------------------------------


def test_parsear_registro_doi_usa_normalizer(harvester: OpenAlexHarvester) -> None:
    work = {**WORK_COMPLETO, "doi": "DOI: 10.1016/j.neunet.2020.01.001"}
    parsed = harvester.parsear_registro(work)
    assert parsed["doi"] == "10.1016/j.neunet.2020.01.001"
    assert "DOI" not in parsed["doi"]


def test_parsear_registro_titulo_normalizado_minusculas(harvester: OpenAlexHarvester) -> None:
    parsed = harvester.parsear_registro(WORK_COMPLETO)
    assert parsed["titulo_normalizado"] == parsed["titulo_normalizado"].lower()


def test_parsear_registro_titulo_normalizado_sin_acentos(harvester: OpenAlexHarvester) -> None:
    parsed = harvester.parsear_registro(WORK_COMPLETO)
    titulo_norm = parsed["titulo_normalizado"] or ""
    for char in "áéíóúÁÉÍÓÚñÑ":
        assert char not in titulo_norm
