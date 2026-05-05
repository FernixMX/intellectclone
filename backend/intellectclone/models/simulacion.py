"""
Modelos SQLAlchemy: simulaciones (Mirrorfish UAT).
Tablas: Simulacion, RespuestaSimulacion

NOTA R5: estas tablas se crean pero NO se usan en v1.
La lógica de simulación se implementa en v1.5.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from intellectclone.db.base import Base
from intellectclone.models.enums import (
    EstadoSimulacion,
    IntensidadRespuesta,
    PosturaRespuesta,
)

if TYPE_CHECKING:
    from intellectclone.models.gemelo import Gemelo
    from intellectclone.models.persona import Persona
    from intellectclone.models.sistema import UsuarioSistema


class Simulacion(Base):
    """Cada escenario lanzado contra una cohorte de gemelos. (v1.5)"""

    __tablename__ = "simulacion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Quién y cuándo
    creada_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # El escenario
    escenario: Mapped[str] = mapped_column(sa.Text, nullable=False)
    contexto_adicional: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Configuración
    modelo_simulacion: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    temperatura: Mapped[float | None] = mapped_column(
        sa.Numeric(3, 2), nullable=True, default=0.7
    )
    max_tokens_respuesta: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True, default=2000
    )
    idioma_respuesta: Mapped[str] = mapped_column(
        sa.String(10), nullable=False, default="es"
    )
    formato_esperado: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="libre"
    )

    # Cohorte
    filtros_cohorte: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    gemelos_seleccionados: Mapped[list] = mapped_column(  # type: ignore[type-arg]
        sa.ARRAY(UUID(as_uuid=True)), nullable=False
    )
    total_gemelos: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    # Estado y métricas
    estado: Mapped[EstadoSimulacion] = mapped_column(
        sa.Enum(EstadoSimulacion, name="estado_simulacion", create_type=False),
        nullable=False,
        default=EstadoSimulacion.borrador,
    )
    progreso_porcentaje: Mapped[int] = mapped_column(
        sa.SmallInteger, nullable=False, default=0
    )

    # Costos
    costo_estimado_usd: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 4), nullable=True
    )
    costo_real_usd: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 4), nullable=True
    )
    tokens_consumidos_total: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # Tiempos
    iniciada_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    completada_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    duracion_ms: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # Síntesis
    sintesis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # type: ignore[type-arg]
    sintesis_generada_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    resumen_ejecutivo: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Acceso
    visibilidad: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default="privada"
    )
    compartida_con: Mapped[list | None] = mapped_column(  # type: ignore[type-arg]
        sa.ARRAY(UUID(as_uuid=True)), nullable=True
    )

    error_mensaje: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    metadatos: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    creador: Mapped["UsuarioSistema"] = relationship(
        "UsuarioSistema",
        back_populates="simulaciones",
        foreign_keys=[creada_por],
        primaryjoin="Simulacion.creada_por == UsuarioSistema.id",
    )
    respuestas: Mapped[list["RespuestaSimulacion"]] = relationship(
        "RespuestaSimulacion", back_populates="simulacion", cascade="all, delete-orphan"
    )


class RespuestaSimulacion(Base):
    """Lo que cada gemelo respondió en una simulación dada. (v1.5)"""

    __tablename__ = "respuesta_simulacion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    simulacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("simulacion.id", ondelete="CASCADE"),
        nullable=False,
    )
    gemelo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("gemelo.id", ondelete="RESTRICT"),
        nullable=False,
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Respuesta cruda
    respuesta_texto: Mapped[str] = mapped_column(sa.Text, nullable=False)

    # Análisis de la respuesta
    postura: Mapped[PosturaRespuesta] = mapped_column(
        sa.Enum(PosturaRespuesta, name="postura_respuesta", create_type=False),
        nullable=False,
        default=PosturaRespuesta.sin_clasificar,
    )
    intensidad: Mapped[IntensidadRespuesta | None] = mapped_column(
        sa.Enum(IntensidadRespuesta, name="intensidad_respuesta", create_type=False),
        nullable=True,
    )
    temas_tocados: Mapped[list[str] | None] = mapped_column(
        sa.ARRAY(sa.Text), nullable=True
    )
    citas_clave: Mapped[list[str] | None] = mapped_column(
        sa.ARRAY(sa.Text), nullable=True
    )
    sentimiento: Mapped[float | None] = mapped_column(sa.Numeric(4, 3), nullable=True)

    # Linaje de la ejecución
    tokens_prompt: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    costo_usd: Mapped[float | None] = mapped_column(sa.Numeric(10, 5), nullable=True)
    duracion_ms: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    modelo_usado: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    # Errores
    error_mensaje: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Embedding de la respuesta
    embedding_respuesta: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )

    metadatos: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (sa.UniqueConstraint("simulacion_id", "gemelo_id"),)

    # Relaciones
    simulacion: Mapped["Simulacion"] = relationship(
        "Simulacion", back_populates="respuestas"
    )
    gemelo: Mapped["Gemelo"] = relationship(
        "Gemelo", back_populates="respuestas_simulacion"
    )
    persona: Mapped["Persona"] = relationship("Persona")
