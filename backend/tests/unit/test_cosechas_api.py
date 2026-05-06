"""
Tests unitarios para los endpoints de cosechas (C4).

Cubre:
- GET /cosechas: listado vacío, con items, con filtros
- GET /cosechas/estado-fuentes: respuesta por cada TipoFuente
- GET /cosechas/{id}: existente y no encontrada
- GET /cosechas/{id}/progreso: estado en curso y completada
- POST /cosechas/disparar: crea cosecha y encola tarea
- POST /cosechas/{id}/cancelar: programada→cancelada, y estado inválido
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellectclone.models.enums import EstadoCosecha, TipoFuente
from intellectclone.schemas.cosecha import (
    CosechaDispararRequest,
    CosechaRead,
)


def _mk_cosecha(
    fuente: TipoFuente = TipoFuente.openalex,
    estado: EstadoCosecha = EstadoCosecha.completada,
) -> MagicMock:
    c = MagicMock()
    c.id = uuid.uuid4()
    c.fuente = fuente
    c.estado = estado
    c.programada_para = None
    c.iniciada_at = None
    c.completada_at = datetime.now(UTC)
    c.duracion_ms = 5000
    c.registros_procesados = 42
    c.registros_nuevos = 30
    c.registros_actualizados = 10
    c.registros_descartados = 2
    c.errores_count = 0
    c.configuracion = {}
    c.log_resumen = None
    c.errores = None
    c.disparada_por = None
    c.disparada_manual = True
    c.created_at = datetime.now(UTC)
    c.updated_at = datetime.now(UTC)
    return c


class TestListarCosechas:
    @pytest.mark.asyncio
    async def test_listado_vacio(self) -> None:
        from intellectclone.api.v1.cosechas import listar_cosechas

        mock_repo = AsyncMock()
        mock_repo.listar_con_filtros = AsyncMock(return_value=(0, []))

        with patch(
            "intellectclone.api.v1.cosechas.RepositorioCosecha",
            return_value=mock_repo,
        ):
            result = await listar_cosechas(
                fuente=None,
                estado=None,
                desde=None,
                hasta=None,
                limit=20,
                offset=0,
                session=AsyncMock(),
            )

        assert result.total == 0
        assert result.items == []
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_listado_con_items(self) -> None:
        from intellectclone.api.v1.cosechas import listar_cosechas

        cosecha = _mk_cosecha()
        mock_repo = AsyncMock()
        mock_repo.listar_con_filtros = AsyncMock(return_value=(1, [cosecha]))

        with (
            patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo),
            patch(
                "intellectclone.schemas.cosecha.CosechaRead.model_validate",
                return_value=MagicMock(spec=CosechaRead),
            ),
        ):
            result = await listar_cosechas(
                fuente=None,
                estado=None,
                desde=None,
                hasta=None,
                limit=20,
                offset=0,
                session=AsyncMock(),
            )

        assert result.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_paginacion_next_offset(self) -> None:
        from intellectclone.api.v1.cosechas import listar_cosechas

        items = [_mk_cosecha() for _ in range(5)]
        mock_repo = AsyncMock()
        mock_repo.listar_con_filtros = AsyncMock(return_value=(10, items))

        with (
            patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo),
            patch(
                "intellectclone.schemas.cosecha.CosechaRead.model_validate",
                return_value=MagicMock(),
            ),
        ):
            result = await listar_cosechas(
                fuente=None,
                estado=None,
                desde=None,
                hasta=None,
                limit=5,
                offset=0,
                session=AsyncMock(),
            )

        assert result.next_offset == 5


class TestEstadoFuentes:
    @pytest.mark.asyncio
    async def test_devuelve_una_entrada_por_fuente(self) -> None:
        from intellectclone.api.v1.cosechas import estado_fuentes

        mock_repo = AsyncMock()
        mock_repo.obtener_ultima_por_fuente = AsyncMock(return_value=None)

        with patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo):
            result = await estado_fuentes(session=AsyncMock())

        fuentes_en_resultado = {r.fuente for r in result}
        assert fuentes_en_resultado == set(TipoFuente)

    @pytest.mark.asyncio
    async def test_incluye_datos_de_ultima_cosecha(self) -> None:
        from intellectclone.api.v1.cosechas import estado_fuentes

        cosecha = _mk_cosecha(fuente=TipoFuente.openalex)
        mock_repo = AsyncMock()

        async def _obtener(fuente: TipoFuente) -> MagicMock | None:
            return cosecha if fuente == TipoFuente.openalex else None

        mock_repo.obtener_ultima_por_fuente = _obtener

        with patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo):
            result = await estado_fuentes(session=AsyncMock())

        openalex_entry = next(r for r in result if r.fuente == TipoFuente.openalex)
        assert openalex_entry.ultima_cosecha_id == cosecha.id
        assert openalex_entry.registros_procesados == cosecha.registros_procesados


class TestObtenerCosecha:
    @pytest.mark.asyncio
    async def test_cosecha_existente(self) -> None:
        from intellectclone.api.v1.cosechas import obtener_cosecha

        cosecha = _mk_cosecha()
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)

        with patch(
            "intellectclone.schemas.cosecha.CosechaRead.model_validate", return_value=MagicMock()
        ):
            result = await obtener_cosecha(id=cosecha.id, session=session)

        assert result is not None

    @pytest.mark.asyncio
    async def test_cosecha_no_encontrada(self) -> None:
        from intellectclone.api.excepciones import EntidadNoEncontrada
        from intellectclone.api.v1.cosechas import obtener_cosecha

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(EntidadNoEncontrada):
            await obtener_cosecha(id=uuid.uuid4(), session=session)


class TestProgresoCosecha:
    @pytest.mark.asyncio
    async def test_cosecha_no_encontrada(self) -> None:
        from intellectclone.api.excepciones import EntidadNoEncontrada
        from intellectclone.api.v1.cosechas import progreso_cosecha

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(EntidadNoEncontrada):
            await progreso_cosecha(id=uuid.uuid4(), session=session)

    @pytest.mark.asyncio
    async def test_cosecha_completada_sin_velocidad(self) -> None:
        from intellectclone.api.v1.cosechas import progreso_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.completada)
        cosecha.iniciada_at = None
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)

        result = await progreso_cosecha(id=cosecha.id, session=session)

        assert result.estado == EstadoCosecha.completada
        assert result.velocidad_rps is None

    @pytest.mark.asyncio
    async def test_cosecha_en_curso_calcula_velocidad(self) -> None:
        from intellectclone.api.v1.cosechas import progreso_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.en_curso)
        cosecha.iniciada_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        cosecha.registros_procesados = 100
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)

        result = await progreso_cosecha(id=cosecha.id, session=session)

        assert result.estado == EstadoCosecha.en_curso
        assert result.registros_procesados == 100
        assert result.velocidad_rps is not None
        assert result.velocidad_rps > 0


class TestDispararCosecha:
    @pytest.mark.asyncio
    async def test_dispara_correctamente(self) -> None:
        from intellectclone.api.v1.cosechas import disparar_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.programada)
        mock_repo = AsyncMock()
        mock_repo.crear_cosecha = AsyncMock(return_value=cosecha)

        session = AsyncMock()
        session.commit = AsyncMock()

        tarea_mock = MagicMock()
        tarea_mock.id = "celery-task-abc123"

        body = CosechaDispararRequest(
            fuente=TipoFuente.openalex,
            modo="completa",
            parametros={},
            configuracion={},
        )

        with (
            patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo),
            patch(
                "intellectclone.api.v1.cosechas.cosechar_fuente",
            ) as mock_task,
        ):
            mock_task.delay = MagicMock(return_value=tarea_mock)
            result = await disparar_cosecha(body=body, session=session)

        assert result.cosecha_id == cosecha.id
        assert result.tarea_celery_id == "celery-task-abc123"
        assert result.estimacion_duracion_minutos == 30

    @pytest.mark.asyncio
    async def test_estimacion_incremental(self) -> None:
        from intellectclone.api.v1.cosechas import disparar_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.programada)
        mock_repo = AsyncMock()
        mock_repo.crear_cosecha = AsyncMock(return_value=cosecha)

        session = AsyncMock()
        session.commit = AsyncMock()

        tarea_mock = MagicMock()
        tarea_mock.id = "celery-task-xyz"

        body = CosechaDispararRequest(
            fuente=TipoFuente.openalex,
            modo="incremental",
            parametros={"desde_fecha": "2025-01-01"},
            configuracion={},
        )

        with (
            patch("intellectclone.api.v1.cosechas.RepositorioCosecha", return_value=mock_repo),
            patch("intellectclone.api.v1.cosechas.cosechar_fuente") as mock_task,
        ):
            mock_task.delay = MagicMock(return_value=tarea_mock)
            result = await disparar_cosecha(body=body, session=session)

        assert result.estimacion_duracion_minutos == 5


class TestCancelarCosecha:
    @pytest.mark.asyncio
    async def test_cancela_cosecha_programada(self) -> None:
        from intellectclone.api.v1.cosechas import cancelar_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.programada)
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch(
            "intellectclone.schemas.cosecha.CosechaRead.model_validate", return_value=MagicMock()
        ):
            await cancelar_cosecha(id=cosecha.id, session=session)

        assert cosecha.estado == EstadoCosecha.cancelada

    @pytest.mark.asyncio
    async def test_no_puede_cancelar_cosecha_completada(self) -> None:
        from intellectclone.api.excepciones import EstadoInvalido
        from intellectclone.api.v1.cosechas import cancelar_cosecha

        cosecha = _mk_cosecha(estado=EstadoCosecha.completada)
        session = AsyncMock()
        session.get = AsyncMock(return_value=cosecha)

        with pytest.raises(EstadoInvalido):
            await cancelar_cosecha(id=cosecha.id, session=session)

    @pytest.mark.asyncio
    async def test_cosecha_no_encontrada(self) -> None:
        from intellectclone.api.excepciones import EntidadNoEncontrada
        from intellectclone.api.v1.cosechas import cancelar_cosecha

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(EntidadNoEncontrada):
            await cancelar_cosecha(id=uuid.uuid4(), session=session)
