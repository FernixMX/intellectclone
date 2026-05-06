"""
BaseHarvester: clase abstracta raíz de todos los cosechadores.

Política de backoff: 1er reintento 60s, 2do 300s, 3er 1800s.
A partir del 4to intento fallido se omite el registro.
Errores de autenticación (401/403 en contexto["status_code"]) abortan inmediatamente.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from intellectclone.harvesters.tipos import (
    AccionIntento,
    NivelError,
    ResultadoCosecha,
    ResultadoIntento,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BACKOFF_DELAYS: dict[int, float] = {1: 60.0, 2: 300.0, 3: 1800.0}
_AUTH_ERRORS: frozenset[int] = frozenset({401, 403})


class BaseHarvester(abc.ABC):
    """Contrato que deben cumplir todos los cosechadores de IntellectClone."""

    nombre: str
    fuente_tipo: str
    rate_limit_requests_por_segundo: float = 1.0

    # ------------------------------------------------------------------
    # Métodos abstractos — cada harvester los implementa
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def configurar(self, config: dict[str, Any]) -> None:
        """Inicializa credenciales, URLs base y demás parámetros del harvester."""

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Verifica que la fuente es alcanzable. True = OK."""

    @abc.abstractmethod
    def cosechar(
        self,
        cosecha_id: str,
        modo: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        """
        Generador asíncrono que emite ResultadoCosecha uno a uno.
        Las implementaciones deben ser funciones `async def` con `yield`.
        """

    @abc.abstractmethod
    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transforma un registro crudo al formato canónico del sistema."""

    # ------------------------------------------------------------------
    # Lógica de error compartida
    # ------------------------------------------------------------------

    def manejar_error(
        self,
        error: Exception,
        contexto: dict[str, Any],
        intento: int,
    ) -> ResultadoIntento:
        """
        Decide qué hacer tras un fallo de cosecha.

        Reglas:
        - status_code 401/403 → abortar de inmediato
        - intentos 1-3 → reintentar con backoff exponencial
        - intento 4+ → omitir registro y continuar
        """
        status_code: Any = contexto.get("status_code")

        if isinstance(status_code, int) and status_code in _AUTH_ERRORS:
            logger.error(
                "harvester.auth_error",
                harvester=self.nombre,
                status_code=status_code,
                cosecha_id=contexto.get("cosecha_id"),
                nivel=NivelError.critical.value,
            )
            return ResultadoIntento(
                accion=AccionIntento.abortar,
                mensaje=f"Error de autenticación {status_code} — cosecha abortada",
            )

        if intento in _BACKOFF_DELAYS:
            delay = _BACKOFF_DELAYS[intento]
            logger.warning(
                "harvester.reintento",
                harvester=self.nombre,
                intento=intento,
                delay_segundos=delay,
                error=str(error),
                nivel=NivelError.warning.value,
            )
            return ResultadoIntento(
                accion=AccionIntento.reintentar,
                delay_segundos=delay,
                mensaje=f"Intento {intento} fallido — reintentando en {delay}s",
            )

        logger.error(
            "harvester.omitiendo_registro",
            harvester=self.nombre,
            intento=intento,
            error=str(error),
            nivel=NivelError.error.value,
        )
        return ResultadoIntento(
            accion=AccionIntento.omitir,
            mensaje=f"Intento {intento} fallido — omitiendo registro",
        )
