"""
Tests unitarios para intellectclone.harvesters.snii_api.
Cubre funciones puras (normalizar_nombre, tipo_dependencia, mapear_nivel_snii,
build_dependencia_values) y los fetch helpers con httpx mockeado.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import httpx
import pytest

from intellectclone.harvesters.snii_api import (
    build_dependencia_values,
    fetch_dependencias,
    fetch_investigadores,
    mapear_nivel_snii,
    normalizar_nombre,
    tipo_dependencia,
)
from intellectclone.models.enums import NivelSnii

# ---------------------------------------------------------------------------
# normalizar_nombre
# ---------------------------------------------------------------------------


class TestNormalizarNombre:
    def test_minusculas(self) -> None:
        assert normalizar_nombre("JUAN PÉREZ") == "juan perez"

    def test_sin_acentos(self) -> None:
        assert normalizar_nombre("García López") == "garcia lopez"

    def test_espacios_colapsados(self) -> None:
        assert normalizar_nombre("  Ana   Luz  ") == "ana luz"

    def test_nombre_vacio(self) -> None:
        assert normalizar_nombre("") == ""

    def test_combinado(self) -> None:
        assert (
            normalizar_nombre("José Ángel Martínez  Hernández") == "jose angel martinez hernandez"
        )


# ---------------------------------------------------------------------------
# tipo_dependencia
# ---------------------------------------------------------------------------


class TestTipoDependencia:
    def test_facultad(self) -> None:
        assert tipo_dependencia("Facultad de Derecho y Ciencias Sociales") == "facultad"

    def test_unidad_academica(self) -> None:
        assert (
            tipo_dependencia("Unidad Académica Multidisciplinaria Río Bravo") == "unidad_academica"
        )

    def test_unidad_academica_sin_acento(self) -> None:
        assert tipo_dependencia("Unidad Academica Reynosa") == "unidad_academica"

    def test_centro(self) -> None:
        assert tipo_dependencia("Centro de Investigación Aplicada") == "centro"

    def test_instituto(self) -> None:
        assert tipo_dependencia("Instituto de Tecnología") == "instituto"

    def test_otro(self) -> None:
        assert tipo_dependencia("Rectoría General") == "otro"


# ---------------------------------------------------------------------------
# mapear_nivel_snii
# ---------------------------------------------------------------------------


class TestMapearNivelSnii:
    @pytest.mark.parametrize(
        "raw,esperado",
        [
            ("Candidato", NivelSnii.candidato.value),
            ("candidato", NivelSnii.candidato.value),
            ("SNCA", NivelSnii.candidato.value),
            ("snca", NivelSnii.candidato.value),
            ("SNII 1", NivelSnii.nivel_1.value),
            ("snii 1", NivelSnii.nivel_1.value),
            ("Nivel I", NivelSnii.nivel_1.value),
            ("SNII 2", NivelSnii.nivel_2.value),
            ("SNII 3", NivelSnii.nivel_3.value),
            ("Emérito", NivelSnii.emerito.value),
            ("emerito", NivelSnii.emerito.value),
        ],
    )
    def test_mapeo_correcto(self, raw: str, esperado: str) -> None:
        assert mapear_nivel_snii(raw) == esperado

    def test_desconocido_devuelve_none(self) -> None:
        assert mapear_nivel_snii("CONACYT Senior") is None

    def test_vacio_devuelve_none(self) -> None:
        assert mapear_nivel_snii("") is None


# ---------------------------------------------------------------------------
# build_dependencia_values
# ---------------------------------------------------------------------------


class TestBuildDependenciaValues:
    def test_codigo_incluye_id(self) -> None:
        dep = {"id": "16", "nombre": "Facultad de Comercio Victoria", "campus": "Victoria"}
        vals = build_dependencia_values(dep)
        assert vals["codigo"] == "SNII-16"

    def test_tipo_inferido(self) -> None:
        dep = {"id": "1", "nombre": "Facultad de Medicina", "campus": "Victoria"}
        vals = build_dependencia_values(dep)
        assert vals["tipo"] == "facultad"

    def test_campus_preservado(self) -> None:
        dep = {"id": "5", "nombre": "Unidad Académica Matamoros", "campus": "Matamoros"}
        vals = build_dependencia_values(dep)
        assert vals["campus"] == "Matamoros"

    def test_campus_vacio_es_none(self) -> None:
        dep = {"id": "5", "nombre": "Facultad X", "campus": ""}
        vals = build_dependencia_values(dep)
        assert vals["campus"] is None

    def test_activa_es_true(self) -> None:
        dep = {"id": "1", "nombre": "Facultad X", "campus": "V"}
        assert build_dependencia_values(dep)["activa"] is True

    def test_id_es_uuid(self) -> None:
        dep = {"id": "1", "nombre": "Facultad X", "campus": "V"}
        val_id = build_dependencia_values(dep)["id"]
        assert isinstance(val_id, uuid.UUID)

    def test_metadatos_vacio(self) -> None:
        dep = {"id": "1", "nombre": "Facultad X", "campus": "V"}
        assert build_dependencia_values(dep)["metadatos"] == {}


# ---------------------------------------------------------------------------
# fetch_investigadores / fetch_dependencias (httpx mockeado)
# ---------------------------------------------------------------------------

_FAKE_INVESTIGADORES = [
    {"id": "1", "nombre": "Juan García", "sni": "SNII 1", "campus": "Facultad A", "area": "1"},
    {"id": "2", "nombre": "Ana López", "sni": "Candidato", "campus": "Facultad B", "area": "2"},
]

_FAKE_DEPENDENCIAS = [
    {"id": "10", "nombre": "Facultad de Ciencias Victoria", "campus": "Victoria", "idCampus": "1"},
]


def _mock_response(data: object) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"d": json.dumps(data)})
    return resp


class TestFetchInvestigadores:
    def test_retorna_lista(self) -> None:
        with patch(
            "intellectclone.harvesters.snii_api.httpx.post",
            return_value=_mock_response(_FAKE_INVESTIGADORES),
        ):
            result = fetch_investigadores(base_url="http://test.local")
        assert len(result) == 2
        assert result[0]["nombre"] == "Juan García"

    def test_llama_endpoint_correcto(self) -> None:
        with patch(
            "intellectclone.harvesters.snii_api.httpx.post", return_value=_mock_response([])
        ) as mock_post:
            fetch_investigadores(base_url="http://test.local")
        mock_post.assert_called_once()
        assert "buscador.aspx/Filtrado" in mock_post.call_args[0][0]

    def test_propaga_http_error(self) -> None:
        resp = MagicMock(spec=httpx.Response)
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=MagicMock())
        )
        with (
            patch("intellectclone.harvesters.snii_api.httpx.post", return_value=resp),
            pytest.raises(httpx.HTTPStatusError),
        ):
            fetch_investigadores()


class TestFetchDependencias:
    def test_retorna_lista(self) -> None:
        with patch(
            "intellectclone.harvesters.snii_api.httpx.post",
            return_value=_mock_response(_FAKE_DEPENDENCIAS),
        ):
            result = fetch_dependencias(base_url="http://test.local")
        assert len(result) == 1
        assert result[0]["nombre"] == "Facultad de Ciencias Victoria"

    def test_llama_endpoint_correcto(self) -> None:
        with patch(
            "intellectclone.harvesters.snii_api.httpx.post", return_value=_mock_response([])
        ) as mock_post:
            fetch_dependencias(base_url="http://test.local")
        mock_post.assert_called_once()
        assert "dependencias.aspx/FiltradoDependencias" in mock_post.call_args[0][0]
