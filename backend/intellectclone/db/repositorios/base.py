"""
Repositorio base genérico para operaciones CRUD comunes.
Todos los repositorios de dominio heredan de esta clase.
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.db.base import Base

TModel = TypeVar("TModel", bound=Base)


class RepositorioBase(Generic[TModel]):
    """
    Repositorio base con operaciones CRUD estándar.
    Los repositorios específicos heredan y extienden esta clase.
    """

    def __init__(self, session: AsyncSession, model: type[TModel]) -> None:
        self._session = session
        self._model = model

    async def obtener_por_id(self, id: uuid.UUID) -> TModel | None:
        """Obtiene una entidad por su ID. Devuelve None si no existe."""
        result = await self._session.get(self._model, id)
        return result  # type: ignore[no-any-return]

    async def listar(self, limit: int = 20, offset: int = 0) -> tuple[int, list[TModel]]:
        """
        Lista entidades con paginación.
        Devuelve (total, items).
        """
        # Contar total
        count_stmt = select(func.count()).select_from(self._model)
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Obtener página
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return total, items

    async def crear(self, datos: dict) -> TModel:  # type: ignore[type-arg]
        """Crea una nueva entidad con los datos dados."""
        instancia = self._model(**datos)
        self._session.add(instancia)
        await self._session.flush()
        await self._session.refresh(instancia)
        return instancia

    async def actualizar(self, instancia: TModel, datos: dict) -> TModel:  # type: ignore[type-arg]
        """Actualiza una entidad existente con los datos dados (solo campos no None)."""
        for campo, valor in datos.items():
            if valor is not None:
                setattr(instancia, campo, valor)
        self._session.add(instancia)
        await self._session.flush()
        await self._session.refresh(instancia)
        return instancia

    async def eliminar_logico(self, instancia: TModel) -> TModel:
        """
        Elimina lógicamente una entidad si tiene campo 'activa' o 'activo'.
        Lanza AttributeError si el modelo no soporta baja lógica.
        """
        if hasattr(instancia, "activa"):
            instancia.activa = False
        elif hasattr(instancia, "activo"):
            instancia.activo = False
        else:
            raise AttributeError(
                f"El modelo {self._model.__name__} no tiene campo 'activa' ni 'activo'."
            )
        self._session.add(instancia)
        await self._session.flush()
        await self._session.refresh(instancia)
        return instancia
