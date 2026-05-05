"""
Excepciones de dominio de IntellectClone y su traducción a HTTP (RFC 7807).
Los endpoints capturan estas excepciones y retornan Problem Detail responses.
"""

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse


# =============================================================================
# Jerarquía de excepciones de dominio
# =============================================================================


class IntellectCloneError(Exception):
    """Clase base para todos los errores de dominio de IntellectClone."""

    pass


class EntidadNoEncontrada(IntellectCloneError):
    """La entidad solicitada no existe en la base de datos."""

    def __init__(self, entity_type: str, entity_id: uuid.UUID) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con id={entity_id} no encontrado.")


class EntidadDuplicada(IntellectCloneError):
    """Intento de crear una entidad que viola una restricción de unicidad."""

    def __init__(self, entity_type: str, campo: str, valor: str) -> None:
        self.entity_type = entity_type
        self.campo = campo
        self.valor = valor
        super().__init__(
            f"{entity_type} con {campo}='{valor}' ya existe."
        )


class PermisoInsuficiente(IntellectCloneError):
    """El usuario no tiene permisos para realizar esta operación."""

    def __init__(self, operacion: str) -> None:
        self.operacion = operacion
        super().__init__(f"Permiso insuficiente para: {operacion}")


class EstadoInvalido(IntellectCloneError):
    """La operación no es válida en el estado actual de la entidad."""

    def __init__(self, entity_type: str, estado_actual: str, operacion: str) -> None:
        self.entity_type = entity_type
        self.estado_actual = estado_actual
        self.operacion = operacion
        super().__init__(
            f"{entity_type} en estado '{estado_actual}' no permite: {operacion}"
        )


class PresupuestoExcedido(IntellectCloneError):
    """El costo estimado de la operación supera el presupuesto disponible."""

    def __init__(self, costo_estimado: float, presupuesto_disponible: float) -> None:
        self.costo_estimado = costo_estimado
        self.presupuesto_disponible = presupuesto_disponible
        super().__init__(
            f"Costo estimado ${costo_estimado:.4f} supera el presupuesto "
            f"disponible ${presupuesto_disponible:.4f}"
        )


# =============================================================================
# Handlers para FastAPI (RFC 7807 Problem Details)
# =============================================================================


async def handler_entidad_no_encontrada(
    request: Request, exc: EntidadNoEncontrada
) -> JSONResponse:
    """Traduce EntidadNoEncontrada a HTTP 404 con Problem Detail."""
    return JSONResponse(
        status_code=404,
        content={
            "type": "https://intellectclone.uat.edu.mx/errors/entidad-no-encontrada",
            "title": "Entidad no encontrada",
            "status": 404,
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "entity_id": str(exc.entity_id),
            "instance": str(request.url),
        },
        headers={"Content-Type": "application/problem+json"},
    )


async def handler_entidad_duplicada(
    request: Request, exc: EntidadDuplicada
) -> JSONResponse:
    """Traduce EntidadDuplicada a HTTP 409 con Problem Detail."""
    return JSONResponse(
        status_code=409,
        content={
            "type": "https://intellectclone.uat.edu.mx/errors/entidad-duplicada",
            "title": "Entidad duplicada",
            "status": 409,
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "campo": exc.campo,
            "instance": str(request.url),
        },
        headers={"Content-Type": "application/problem+json"},
    )


async def handler_permiso_insuficiente(
    request: Request, exc: PermisoInsuficiente
) -> JSONResponse:
    """Traduce PermisoInsuficiente a HTTP 403 con Problem Detail."""
    return JSONResponse(
        status_code=403,
        content={
            "type": "https://intellectclone.uat.edu.mx/errors/permiso-insuficiente",
            "title": "Permiso insuficiente",
            "status": 403,
            "detail": str(exc),
            "instance": str(request.url),
        },
        headers={"Content-Type": "application/problem+json"},
    )


async def handler_estado_invalido(
    request: Request, exc: EstadoInvalido
) -> JSONResponse:
    """Traduce EstadoInvalido a HTTP 422 con Problem Detail."""
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://intellectclone.uat.edu.mx/errors/estado-invalido",
            "title": "Estado inválido para esta operación",
            "status": 422,
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "estado_actual": exc.estado_actual,
            "instance": str(request.url),
        },
        headers={"Content-Type": "application/problem+json"},
    )


async def handler_presupuesto_excedido(
    request: Request, exc: PresupuestoExcedido
) -> JSONResponse:
    """Traduce PresupuestoExcedido a HTTP 402 con Problem Detail."""
    return JSONResponse(
        status_code=402,
        content={
            "type": "https://intellectclone.uat.edu.mx/errors/presupuesto-excedido",
            "title": "Presupuesto LLM excedido",
            "status": 402,
            "detail": str(exc),
            "costo_estimado": exc.costo_estimado,
            "presupuesto_disponible": exc.presupuesto_disponible,
            "instance": str(request.url),
        },
        headers={"Content-Type": "application/problem+json"},
    )


def registrar_handlers(app: "FastAPI") -> None:  # type: ignore[name-defined]  # noqa: F821
    """
    Registra todos los exception handlers de dominio en la aplicación FastAPI.
    Llamar desde main.py al crear la app.
    """
    app.add_exception_handler(EntidadNoEncontrada, handler_entidad_no_encontrada)  # type: ignore[arg-type]
    app.add_exception_handler(EntidadDuplicada, handler_entidad_duplicada)  # type: ignore[arg-type]
    app.add_exception_handler(PermisoInsuficiente, handler_permiso_insuficiente)  # type: ignore[arg-type]
    app.add_exception_handler(EstadoInvalido, handler_estado_invalido)  # type: ignore[arg-type]
    app.add_exception_handler(PresupuestoExcedido, handler_presupuesto_excedido)  # type: ignore[arg-type]
