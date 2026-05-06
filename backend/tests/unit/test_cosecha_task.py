"""
Tests unitarios para la tarea Celery cosechar_fuente (C4).

Cubre:
- _ejecutar_cosecha_async: flujo feliz (completada, completada_con_errores)
- _ejecutar_cosecha_async: cosecha no encontrada en DB
- _ejecutar_cosecha_async: ejecutar_cosecha lanza excepción → estado fallida
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellectclone.models.enums import EstadoCosecha, TipoFuente
from intellectclone.tasks.cosecha import _ejecutar_cosecha_async


def _mk_cosecha(estado: EstadoCosecha = EstadoCosecha.programada) -> MagicMock:
    cosecha = MagicMock()
    cosecha.id = "aaaaaaaa-0000-0000-0000-000000000001"
    cosecha.fuente = TipoFuente.openalex
    cosecha.estado = estado
    cosecha.registros_procesados = 0
    cosecha.registros_nuevos = 0
    cosecha.errores_count = 0
    cosecha.iniciada_at = None
    cosecha.log_resumen = None
    return cosecha


@pytest.fixture()
def cosecha_id() -> str:
    return "aaaaaaaa-0000-0000-0000-000000000001"


class TestEjecutarCosechaAsync:
    @pytest.mark.asyncio
    async def test_flujo_feliz_completada(self, cosecha_id: str) -> None:
        cosecha = _mk_cosecha()
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)
        session.commit = AsyncMock()

        factory = MagicMock()
        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=session)
        ctx_mgr.__aexit__ = AsyncMock(return_value=None)
        factory.return_value = ctx_mgr

        resumen_mock = {"total": 10, "nuevos": 8, "errores": 0}

        with (
            patch("intellectclone.tasks.cosecha._get_session_factory", return_value=factory),
            patch(
                "intellectclone.tasks.cosecha.ejecutar_cosecha",
                new_callable=AsyncMock,
                return_value=resumen_mock,
            ),
        ):
            resultado = await _ejecutar_cosecha_async(
                tarea_id="tarea-123",
                cosecha_id=cosecha_id,
                fuente_tipo=TipoFuente.openalex.value,
                modo="completa",
                parametros={},
                config={},
            )

        assert resultado["total"] == 10
        assert resultado["nuevos"] == 8
        assert resultado["errores"] == 0
        assert cosecha.estado == EstadoCosecha.completada

    @pytest.mark.asyncio
    async def test_flujo_completada_con_errores(self, cosecha_id: str) -> None:
        cosecha = _mk_cosecha()
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)
        session.commit = AsyncMock()

        factory = MagicMock()
        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=session)
        ctx_mgr.__aexit__ = AsyncMock(return_value=None)
        factory.return_value = ctx_mgr

        resumen_mock = {"total": 5, "nuevos": 3, "errores": 2}

        with (
            patch("intellectclone.tasks.cosecha._get_session_factory", return_value=factory),
            patch(
                "intellectclone.tasks.cosecha.ejecutar_cosecha",
                new_callable=AsyncMock,
                return_value=resumen_mock,
            ),
        ):
            resultado = await _ejecutar_cosecha_async(
                tarea_id=None,
                cosecha_id=cosecha_id,
                fuente_tipo=TipoFuente.openalex.value,
                modo="incremental",
                parametros={"desde_fecha": "2024-01-01"},
                config={},
            )

        assert resultado["errores"] == 2
        assert cosecha.estado == EstadoCosecha.completada_con_errores

    @pytest.mark.asyncio
    async def test_cosecha_no_encontrada_en_db(self, cosecha_id: str) -> None:
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)
        session.commit = AsyncMock()

        factory = MagicMock()
        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=session)
        ctx_mgr.__aexit__ = AsyncMock(return_value=None)
        factory.return_value = ctx_mgr

        with (
            patch("intellectclone.tasks.cosecha._get_session_factory", return_value=factory),
            pytest.raises(ValueError, match="no encontrada en DB"),
        ):
            await _ejecutar_cosecha_async(
                tarea_id=None,
                cosecha_id=cosecha_id,
                fuente_tipo=TipoFuente.openalex.value,
                modo="completa",
                parametros={},
                config={},
            )

    @pytest.mark.asyncio
    async def test_ejecutar_cosecha_falla_marca_estado_fallida(self, cosecha_id: str) -> None:
        cosecha = _mk_cosecha()
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)
        session.commit = AsyncMock()

        factory = MagicMock()
        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=session)
        ctx_mgr.__aexit__ = AsyncMock(return_value=None)
        factory.return_value = ctx_mgr

        with (
            patch("intellectclone.tasks.cosecha._get_session_factory", return_value=factory),
            patch(
                "intellectclone.tasks.cosecha.ejecutar_cosecha",
                new_callable=AsyncMock,
                side_effect=RuntimeError("error de red"),
            ),
            pytest.raises(RuntimeError, match="error de red"),
        ):
            await _ejecutar_cosecha_async(
                tarea_id=None,
                cosecha_id=cosecha_id,
                fuente_tipo=TipoFuente.openalex.value,
                modo="completa",
                parametros={},
                config={},
            )

        assert cosecha.estado == EstadoCosecha.fallida
        assert cosecha.log_resumen == "error de red"
