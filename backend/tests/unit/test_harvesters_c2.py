"""
Tests unitarios para C2: normalizer, disambiguator, deduplicator.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from intellectclone.harvesters.deduplicator import (
    _consolidar_metadatos,
    _nombres_coinciden,
    _obtener_primer_autor,
    deduplicar_paper,
)
from intellectclone.harvesters.disambiguator import (
    ROR_UAT,
    _autor_en_uat,
    _extraer_openalex_author_id,
    _limpiar_orcid,
    desambiguar_autor,
)
from intellectclone.harvesters.normalizer import (
    normalizar_doi,
    normalizar_nombre,
    normalizar_titulo,
    ratio_similitud,
)

# ===========================================================================
# NORMALIZER
# ===========================================================================


class TestNormalizarNombre:
    def test_minusculas(self) -> None:
        assert normalizar_nombre("JUAN PÉREZ") == "juan perez"

    def test_acentos(self) -> None:
        assert normalizar_nombre("María Ángel") == "maria angel"

    def test_guion_a_espacio(self) -> None:
        assert normalizar_nombre("Cárdenas-Ruiz") == "cardenas ruiz"

    def test_punto_a_espacio(self) -> None:
        assert normalizar_nombre("J. García") == "j garcia"

    def test_espacios_multiples(self) -> None:
        assert normalizar_nombre("Ana  López") == "ana lopez"

    def test_cadena_vacia(self) -> None:
        assert normalizar_nombre("") == ""

    def test_ejemplo_doc(self) -> None:
        assert normalizar_nombre("María Elena Cárdenas-Ruiz") == "maria elena cardenas ruiz"


class TestNormalizarTitulo:
    def test_elimina_puntuacion(self) -> None:
        result = normalizar_titulo("Análisis: un enfoque nuevo (2020)")
        assert ":" not in result
        assert "(" not in result

    def test_solo_alfanumerico_y_espacios(self) -> None:
        result = normalizar_titulo("Hello, world! #1")
        assert all(c.isalnum() or c == " " for c in result)

    def test_minusculas_sin_acentos(self) -> None:
        result = normalizar_titulo("Redes Neuronales Artificiales")
        assert result == "redes neuronales artificiales"


class TestNormalizarDoi:
    def test_prefijo_https(self) -> None:
        assert normalizar_doi("https://doi.org/10.1016/j.foo") == "10.1016/j.foo"

    def test_prefijo_http(self) -> None:
        assert normalizar_doi("http://doi.org/10.1016/j.foo") == "10.1016/j.foo"

    def test_prefijo_dx(self) -> None:
        assert normalizar_doi("https://dx.doi.org/10.1016/j.foo") == "10.1016/j.foo"

    def test_prefijo_doi_colon(self) -> None:
        assert normalizar_doi("DOI: 10.1016/j.foo") == "10.1016/j.foo"

    def test_ya_limpio(self) -> None:
        assert normalizar_doi("10.1016/j.foo") == "10.1016/j.foo"

    def test_mayusculas_a_minusculas(self) -> None:
        assert normalizar_doi("10.1016/J.FOO") == "10.1016/j.foo"


class TestRatioSimilitud:
    def test_identicas(self) -> None:
        assert ratio_similitud("hola mundo", "hola mundo") == 1.0

    def test_completamente_distintas(self) -> None:
        assert ratio_similitud("abc", "xyz") < 0.5

    def test_similares(self) -> None:
        score = ratio_similitud("redes neuronales", "redes neurales")
        assert 0.7 < score < 1.0

    def test_cadena_vacia(self) -> None:
        assert ratio_similitud("", "algo") == 0.0
        assert ratio_similitud("algo", "") == 0.0


# ===========================================================================
# DISAMBIGUATOR — helpers puros
# ===========================================================================


class TestLimpiarOrcid:
    def test_quita_prefijo(self) -> None:
        assert _limpiar_orcid("https://orcid.org/0000-0001-2345-6789") == "0000-0001-2345-6789"

    def test_ya_limpio(self) -> None:
        assert _limpiar_orcid("0000-0001-2345-6789") == "0000-0001-2345-6789"


class TestExtraerOpenalexAuthorId:
    def test_extrae_id(self) -> None:
        assert _extraer_openalex_author_id({"id": "https://openalex.org/A123456"}) == "A123456"

    def test_sin_id(self) -> None:
        assert _extraer_openalex_author_id({}) is None

    def test_id_vacio(self) -> None:
        assert _extraer_openalex_author_id({"id": ""}) is None


class TestAutorEnUAT:
    def test_ror_uat_presente(self) -> None:
        instituciones = [{"ror": ROR_UAT, "display_name": "UAT"}]
        assert _autor_en_uat(instituciones) is True

    def test_ror_distinto(self) -> None:
        instituciones = [{"ror": "https://ror.org/otro"}]
        assert _autor_en_uat(instituciones) is False

    def test_lista_vacia(self) -> None:
        assert _autor_en_uat([]) is False


# ===========================================================================
# DISAMBIGUATOR — desambiguar_autor (async)
# ===========================================================================


def _mk_persona(
    *,
    orcid: str | None = None,
    openalex_id: str | None = None,
    nombre_normalizado: str = "juan perez",
    dependencia_id: uuid.UUID | None = None,
) -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.orcid = orcid
    p.openalex_id = openalex_id
    p.nombre_normalizado = nombre_normalizado
    p.dependencia_id = dependencia_id
    return p


def _mk_session(
    scalar_result: Any = None,
    scalars_list: list[Any] | None = None,
) -> AsyncMock:
    session = AsyncMock()
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = scalar_result
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = scalars_list or []
    scalar_mock.scalars.return_value = scalars_mock
    session.execute = AsyncMock(return_value=scalar_mock)
    return session


@pytest.mark.asyncio
async def test_desambiguar_por_orcid() -> None:
    persona = _mk_persona(orcid="0000-0001-2345-6789", openalex_id="A123")
    session = _mk_session(scalar_result=persona)

    authorship = {
        "author": {
            "orcid": "https://orcid.org/0000-0001-2345-6789",
            "id": "https://openalex.org/A123",
            "display_name": "Juan Pérez",
        },
        "institutions": [],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "orcid"
    assert resultado.confianza == 1.0
    assert resultado.persona_id == persona.id
    assert resultado.requiere_revision is False


@pytest.mark.asyncio
async def test_desambiguar_por_orcid_actualiza_openalex_id() -> None:
    persona = _mk_persona(orcid="0000-0001-2345-6789", openalex_id=None)
    session = _mk_session(scalar_result=persona)

    authorship = {
        "author": {
            "orcid": "https://orcid.org/0000-0001-2345-6789",
            "id": "https://openalex.org/A999",
            "display_name": "Juan Pérez",
        },
        "institutions": [],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "orcid"
    assert resultado.datos_orcid_actualizar.get("openalex_id") == "A999"


@pytest.mark.asyncio
async def test_desambiguar_por_openalex_id() -> None:
    persona = _mk_persona(openalex_id="A555")

    session = AsyncMock()
    # ORCID es None → nivel 1 no llama execute.
    # Primera (y única) llamada es para OpenAlex ID → devuelve persona.
    mock_hit = MagicMock()
    mock_hit.scalar_one_or_none.return_value = persona
    session.execute = AsyncMock(return_value=mock_hit)

    authorship = {
        "author": {
            "orcid": None,
            "id": "https://openalex.org/A555",
            "display_name": "Ana López",
        },
        "institutions": [],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "openalex_id"
    assert resultado.confianza == 0.95
    assert resultado.persona_id == persona.id


@pytest.mark.asyncio
async def test_desambiguar_fuzzy_confiable() -> None:
    persona = _mk_persona(nombre_normalizado="maria garcia lopez", dependencia_id=uuid.uuid4())
    session = AsyncMock()
    # ORCID=None, OpenAlex ID=None → solo se hace la llamada fuzzy (1 execute).
    mock_candidatos = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = [persona]
    mock_candidatos.scalars.return_value = scalars
    session.execute = AsyncMock(return_value=mock_candidatos)

    authorship = {
        "author": {
            "orcid": None,
            "id": None,
            "display_name": "María García López",
        },
        "institutions": [{"ror": ROR_UAT}],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "fuzzy"
    assert resultado.confianza >= 0.95
    assert resultado.persona_id == persona.id


@pytest.mark.asyncio
async def test_desambiguar_fuzzy_requiere_revision() -> None:
    # "maria garcia hernandez" vs "maria garcia hernandez santos" → ratio≈0.863, zona revisión.
    persona = _mk_persona(nombre_normalizado="maria garcia hernandez")
    session = AsyncMock()
    # ORCID=None, OpenAlex ID=None → solo fuzzy.
    mock_candidatos = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = [persona]
    mock_candidatos.scalars.return_value = scalars
    session.execute = AsyncMock(return_value=mock_candidatos)

    authorship = {
        "author": {
            "orcid": None,
            "id": None,
            "display_name": "María García Hernández Santos",
        },
        "institutions": [],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "revision_pendiente"
    assert resultado.requiere_revision is True
    assert resultado.persona_id is None
    assert resultado.candidato_revision_id == persona.id


@pytest.mark.asyncio
async def test_desambiguar_nuevo() -> None:
    session = AsyncMock()
    mock_none = MagicMock()
    mock_none.scalar_one_or_none.return_value = None
    mock_vacio = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = []
    mock_vacio.scalars.return_value = scalars
    session.execute = AsyncMock(side_effect=[mock_none, mock_none, mock_vacio])

    authorship = {
        "author": {"orcid": None, "id": None, "display_name": "Desconocido Nadie"},
        "institutions": [],
    }
    resultado = await desambiguar_autor(authorship, session)
    assert resultado.metodo == "nuevo"
    assert resultado.persona_id is None


# ===========================================================================
# DEDUPLICATOR — helpers puros
# ===========================================================================


class TestObtenerPrimerAutor:
    def test_formato_openalex(self) -> None:
        paper = {
            "autorships": [
                {"author": {"display_name": "Juan Pérez"}},
                {"author": {"display_name": "Ana López"}},
            ]
        }
        assert _obtener_primer_autor(paper) == "juan perez"

    def test_formato_autores(self) -> None:
        paper = {"autores": [{"nombre": "Ana López"}]}
        assert _obtener_primer_autor(paper) == "ana lopez"

    def test_sin_autores(self) -> None:
        assert _obtener_primer_autor({}) == ""


class TestNombresCoinciden:
    def test_identicos(self) -> None:
        assert _nombres_coinciden("juan perez", "juan perez") is True

    def test_muy_distintos(self) -> None:
        assert _nombres_coinciden("juan perez", "ana lopez") is False

    def test_umbral_personalizado(self) -> None:
        assert _nombres_coinciden("juan perez garcia", "juan perez", umbral=0.7) is True


# ===========================================================================
# DEDUPLICATOR — consolidar_metadatos
# ===========================================================================


def _mk_paper(
    doi: str | None = None,
    openalex_id: str | None = None,
    handle_riuat: str | None = None,
    titulo: str = "Paper Test",
    titulo_normalizado: str | None = None,
    año: int | None = 2020,
    abstract: str | None = None,
    fuente_origen: Any = None,
    metadatos: dict[str, Any] | None = None,
) -> MagicMock:
    p = MagicMock(
        spec=[
            "doi",
            "openalex_id",
            "handle_riuat",
            "titulo",
            "titulo_normalizado",
            "año",
            "abstract",
            "url_pdf",
            "fuente_origen",
            "metadatos",
            "coautorias",
            "id",
        ]
    )
    p.id = uuid.uuid4()
    p.doi = doi
    p.openalex_id = openalex_id
    p.handle_riuat = handle_riuat
    p.titulo = titulo
    p.titulo_normalizado = titulo_normalizado
    p.año = año
    p.abstract = abstract
    p.url_pdf = None
    p.fuente_origen = fuente_origen
    p.metadatos = metadatos or {}
    p.coautorias = []
    return p


def test_consolidar_metadatos_llena_nulos() -> None:
    from intellectclone.models.enums import TipoFuente

    existente = _mk_paper(abstract=None, fuente_origen=TipoFuente.riuat)
    nuevo = {
        "abstract": "Este es el abstract.",
        "fuente_origen": TipoFuente.openalex.value,
        "doi": None,
        "titulo_normalizado": None,
        "url_pdf": None,
    }
    _consolidar_metadatos(existente, nuevo)
    assert existente.abstract == "Este es el abstract."


def test_consolidar_metadatos_registra_fuente_secundaria() -> None:
    from intellectclone.models.enums import TipoFuente

    existente = _mk_paper(fuente_origen=TipoFuente.openalex, metadatos={})
    nuevo = {"fuente_origen": TipoFuente.vufind_uat.value}
    _consolidar_metadatos(existente, nuevo)
    assert "vufind_uat" in existente.metadatos.get("fuentes_secundarias", [])


def test_consolidar_metadatos_no_duplica_fuentes() -> None:
    from intellectclone.models.enums import TipoFuente

    existente = _mk_paper(
        fuente_origen=TipoFuente.openalex,
        metadatos={"fuentes_secundarias": ["vufind_uat"]},
    )
    nuevo = {"fuente_origen": TipoFuente.vufind_uat.value}
    _consolidar_metadatos(existente, nuevo)
    fuentes = existente.metadatos["fuentes_secundarias"]
    assert fuentes.count("vufind_uat") == 1


# ===========================================================================
# DEDUPLICATOR — deduplicar_paper (async)
# ===========================================================================


@pytest.mark.asyncio
async def test_deduplicar_por_doi() -> None:
    paper_existente = _mk_paper(doi="10.1016/j.foo.2020", openalex_id="W111")

    session = AsyncMock()
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = paper_existente
    session.execute = AsyncMock(return_value=mock)

    resultado = await deduplicar_paper(
        {"doi": "https://doi.org/10.1016/j.foo.2020", "fuente_origen": "vufind_uat"},
        session,
    )
    assert resultado.es_duplicado is True
    assert resultado.metodo == "doi"
    assert resultado.paper_id == paper_existente.id


@pytest.mark.asyncio
async def test_deduplicar_por_openalex_id() -> None:
    paper_existente = _mk_paper(openalex_id="W222")

    session = AsyncMock()
    # doi=None → nivel 1 no llama execute.
    # Primera (y única) llamada es para openalex_id → devuelve paper_existente.
    mock_hit = MagicMock()
    mock_hit.scalar_one_or_none.return_value = paper_existente
    session.execute = AsyncMock(return_value=mock_hit)

    resultado = await deduplicar_paper({"doi": None, "openalex_id": "W222"}, session)
    assert resultado.es_duplicado is True
    assert resultado.metodo == "openalex_id"


@pytest.mark.asyncio
async def test_deduplicar_por_handle_riuat() -> None:
    paper_existente = _mk_paper(handle_riuat="http://riuat.uat.edu.mx/handle/123")

    session = AsyncMock()
    # doi=None, openalex_id=None → niveles 1 y 2 no llaman execute.
    # Primera (y única) llamada es para handle_riuat → devuelve paper_existente.
    mock_hit = MagicMock()
    mock_hit.scalar_one_or_none.return_value = paper_existente
    session.execute = AsyncMock(return_value=mock_hit)

    resultado = await deduplicar_paper(
        {"doi": None, "openalex_id": None, "handle_riuat": "http://riuat.uat.edu.mx/handle/123"},
        session,
    )
    assert resultado.es_duplicado is True
    assert resultado.metodo == "handle_riuat"


@pytest.mark.asyncio
async def test_deduplicar_fuzzy_automatico() -> None:
    titulo = "redes neuronales artificiales para clasificacion"
    paper_existente = _mk_paper(
        titulo="Redes Neuronales Artificiales para Clasificación",
        titulo_normalizado=titulo,
        año=2021,
    )
    primer_coautor = MagicMock()
    primer_coautor.orden = 1
    primer_persona = MagicMock()
    primer_persona.nombre_normalizado = "juan perez"
    primer_coautor.persona = primer_persona
    paper_existente.coautorias = [primer_coautor]

    session = AsyncMock()
    # doi=None, openalex_id=None, handle_riuat=None → niveles 1-3 no llaman execute.
    # Primera (y única) llamada es la búsqueda fuzzy por candidatos.
    mock_candidatos = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = [paper_existente]
    mock_candidatos.scalars.return_value = scalars
    session.execute = AsyncMock(return_value=mock_candidatos)

    resultado = await deduplicar_paper(
        {
            "doi": None,
            "openalex_id": None,
            "handle_riuat": None,
            "titulo": "Redes neuronales artificiales para clasificación",
            "año": 2021,
            "autorships": [{"author": {"display_name": "Juan Pérez"}}],
        },
        session,
    )
    assert resultado.es_duplicado is True
    assert resultado.metodo == "fuzzy"
    assert resultado.score >= 0.95


@pytest.mark.asyncio
async def test_deduplicar_nuevo() -> None:
    session = AsyncMock()
    mock_none = MagicMock()
    mock_none.scalar_one_or_none.return_value = None
    mock_vacio = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = []
    mock_vacio.scalars.return_value = scalars
    session.execute = AsyncMock(side_effect=[mock_none, mock_none, mock_none, mock_vacio])

    resultado = await deduplicar_paper(
        {
            "doi": None,
            "openalex_id": None,
            "handle_riuat": None,
            "titulo": "Un paper completamente nuevo y original",
            "año": 2024,
            "autorships": [{"author": {"display_name": "Nadie Conocido"}}],
        },
        session,
    )
    assert resultado.es_duplicado is False
    assert resultado.metodo == "nuevo"
