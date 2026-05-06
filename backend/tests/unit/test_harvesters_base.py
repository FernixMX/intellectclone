"""
Tests unitarios para BaseHarvester, runner y tipos auxiliares.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest

from intellectclone.harvesters.base import _AUTH_ERRORS, _BACKOFF_DELAYS, BaseHarvester
from intellectclone.harvesters.runner import (
    _REGISTRY,
    ejecutar_cosecha,
    obtener_harvester,
    registrar_harvester,
)
from intellectclone.harvesters.tipos import (
    AccionIntento,
    NivelError,
    ResultadoCosecha,
    ResultadoIntento,
)

# ---------------------------------------------------------------------------
# Harvester concreto mínimo para tests
# ---------------------------------------------------------------------------


class HarvesterEjemplo(BaseHarvester):
    nombre = "ejemplo"
    fuente_tipo = "ejemplo"
    rate_limit_requests_por_segundo = 2.0

    def configurar(self, config: dict[str, Any]) -> None:
        self._config = config

    def health_check(self) -> bool:
        return True

    def cosechar(
        self,
        cosecha_id: str,
        modo: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:  # type: ignore[override]
        raise NotImplementedError("usa HarvesterConDatos para tests con yield")

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        return raw_data


class HarvesterConDatos(HarvesterEjemplo):
    """Versión con datos fijos para tests del runner."""

    _resultados: list[ResultadoCosecha] = []

    async def cosechar(  # type: ignore[override]
        self,
        cosecha_id: str,
        modo: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        for r in self._resultados:
            yield r


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------


def test_accion_intento_valores() -> None:
    assert AccionIntento.reintentar == "reintentar"
    assert AccionIntento.omitir == "omitir"
    assert AccionIntento.abortar == "abortar"


def test_nivel_error_orden() -> None:
    niveles = [
        NivelError.debug,
        NivelError.info,
        NivelError.warning,
        NivelError.error,
        NivelError.critical,
    ]
    assert [n.value for n in niveles] == ["debug", "info", "warning", "error", "critical"]


def test_resultado_cosecha_defaults() -> None:
    r = ResultadoCosecha(datos={"x": 1}, fuente_id="abc")
    assert r.es_nuevo is True
    assert r.advertencias == []


def test_resultado_intento_defaults() -> None:
    ri = ResultadoIntento(accion=AccionIntento.omitir)
    assert ri.delay_segundos == 0.0
    assert ri.mensaje == ""


# ---------------------------------------------------------------------------
# manejar_error: política de backoff
# ---------------------------------------------------------------------------


@pytest.fixture()
def harvester() -> HarvesterEjemplo:
    h = HarvesterEjemplo()
    h.configurar({})
    return h


def test_manejar_error_reintento_1(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("fallo"), {}, intento=1)
    assert resultado.accion == AccionIntento.reintentar
    assert resultado.delay_segundos == _BACKOFF_DELAYS[1]


def test_manejar_error_reintento_2(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("fallo"), {}, intento=2)
    assert resultado.accion == AccionIntento.reintentar
    assert resultado.delay_segundos == _BACKOFF_DELAYS[2]


def test_manejar_error_reintento_3(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("fallo"), {}, intento=3)
    assert resultado.accion == AccionIntento.reintentar
    assert resultado.delay_segundos == _BACKOFF_DELAYS[3]


def test_manejar_error_omitir_intento_4(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("fallo"), {}, intento=4)
    assert resultado.accion == AccionIntento.omitir


def test_manejar_error_omitir_intento_alto(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("fallo"), {}, intento=99)
    assert resultado.accion == AccionIntento.omitir


@pytest.mark.parametrize("codigo", list(_AUTH_ERRORS))
def test_manejar_error_aborta_en_auth(harvester: HarvesterEjemplo, codigo: int) -> None:
    resultado = harvester.manejar_error(ValueError("auth"), {"status_code": codigo}, intento=1)
    assert resultado.accion == AccionIntento.abortar


def test_manejar_error_no_aborta_en_500(harvester: HarvesterEjemplo) -> None:
    resultado = harvester.manejar_error(ValueError("server"), {"status_code": 500}, intento=1)
    assert resultado.accion == AccionIntento.reintentar


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registrar_y_obtener_harvester() -> None:
    registrar_harvester("test_fuente_xyz", HarvesterEjemplo)
    clase = obtener_harvester("test_fuente_xyz")
    assert clase is HarvesterEjemplo
    del _REGISTRY["test_fuente_xyz"]


def test_obtener_harvester_no_registrado() -> None:
    with pytest.raises(KeyError, match="fuente_tipo"):
        obtener_harvester("fuente_inexistente_abc123")


# ---------------------------------------------------------------------------
# ejecutar_cosecha: flujo feliz
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ejecutar_cosecha_sin_resultados() -> None:
    registrar_harvester("vacio_test", HarvesterConDatos)
    HarvesterConDatos._resultados = []

    session = MagicMock()
    session.add = MagicMock()

    resumen = await ejecutar_cosecha(
        cosecha_id="cosecha-001",
        fuente_tipo="vacio_test",
        modo="total",
        parametros={},
        config={},
        session=session,
    )

    assert resumen["total"] == 0
    assert resumen["nuevos"] == 0
    assert resumen["errores"] == 0
    del _REGISTRY["vacio_test"]


@pytest.mark.asyncio
async def test_ejecutar_cosecha_con_resultados() -> None:
    registrar_harvester("datos_test", HarvesterConDatos)
    HarvesterConDatos._resultados = [
        ResultadoCosecha(datos={"id": "1"}, fuente_id="f1", es_nuevo=True),
        ResultadoCosecha(datos={"id": "2"}, fuente_id="f2", es_nuevo=False),
        ResultadoCosecha(datos={"id": "3"}, fuente_id="f3", es_nuevo=True),
    ]

    session = MagicMock()
    resumen = await ejecutar_cosecha(
        cosecha_id="cosecha-002",
        fuente_tipo="datos_test",
        modo="incremental",
        parametros={},
        config={},
        session=session,
    )

    assert resumen["total"] == 3
    assert resumen["nuevos"] == 2
    assert resumen["errores"] == 0
    del _REGISTRY["datos_test"]
