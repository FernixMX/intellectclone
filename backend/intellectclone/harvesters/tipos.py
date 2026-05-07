"""
Tipos de datos auxiliares para el sistema de cosecha de IntellectClone.
ResultadoCosecha, ResultadoIntento y enumeraciones de control.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class AccionIntento(str, enum.Enum):
    """Decisión del manejador de errores tras un fallo de cosecha."""

    reintentar = "reintentar"
    omitir = "omitir"
    abortar = "abortar"


class NivelError(str, enum.Enum):
    """Severidad de un evento de error durante la cosecha."""

    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


@dataclass
class ResultadoCosecha:
    """
    Un registro emitido por BaseHarvester.cosechar() en cada yield.
    Los datos ya están parseados al formato canónico del sistema.
    """

    datos: dict[str, Any]
    fuente_id: str
    es_nuevo: bool = True
    advertencias: list[str] = field(default_factory=list)


@dataclass
class ResultadoIntento:
    """Decisión y parámetros del manejador de errores tras un fallo."""

    accion: AccionIntento
    delay_segundos: float = 0.0
    mensaje: str = ""
