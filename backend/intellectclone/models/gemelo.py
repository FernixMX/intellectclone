"""
Modelos SQLAlchemy: gemelos digitales.
Tablas: Gemelo, GemeloCorpusUso
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from intellectclone.db.base import Base
from intellectclone.models.enums import EstadoGemelo, NivelRasgo

if TYPE_CHECKING:
    from intellectclone.models.persona import Persona
    from intellectclone.models.produccion import DocumentoCorpus, Paper
    from intellectclone.models.simulacion import RespuestaSimulacion


class Gemelo(Base):
    """Cada versión del gemelo digital de una persona."""

    __tablename__ = "gemelo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    es_version_actual: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    estado: Mapped[EstadoGemelo] = mapped_column(
        sa.Enum(EstadoGemelo, name="estado_gemelo", create_type=False),
        nullable=False,
        default=EstadoGemelo.borrador,
    )

    # Núcleo HEXACO
    rasgo_extraversion: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rasgo_neuroticismo: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rasgo_responsabilidad: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rasgo_amabilidad: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rasgo_apertura: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rasgo_honestidad_humildad: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Niveles desnormalizados para queries rápidos
    nivel_extraversion: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )
    nivel_neuroticismo: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )
    nivel_responsabilidad: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )
    nivel_amabilidad: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )
    nivel_apertura: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )
    nivel_honestidad_humildad: Mapped[NivelRasgo | None] = mapped_column(
        sa.Enum(NivelRasgo, name="nivel_rasgo", create_type=False),
        nullable=True,
    )

    # Idiolecto
    idiolecto: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Posturas temáticas
    posturas_tematicas: Mapped[list] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )

    # Valores Schwartz (confirmado por Fernando, va en primera migración)
    valores_schwartz: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # System prompt operativo
    system_prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)

    # Score de veracidad y calidad
    score_veracidad: Mapped[float | None] = mapped_column(sa.Numeric(4, 3), nullable=True)
    score_completitud: Mapped[float | None] = mapped_column(sa.Numeric(4, 3), nullable=True)
    score_consistencia: Mapped[float | None] = mapped_column(sa.Numeric(4, 3), nullable=True)

    # Linaje de generación
    modelo_perfilador: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    prompt_perfilador_version: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    tokens_consumidos: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    costo_generacion_usd: Mapped[float | None] = mapped_column(sa.Numeric(10, 4), nullable=True)
    duracion_generacion_ms: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # Validación humana
    validado_por_persona: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    fecha_validacion: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    comentarios_validacion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Embedding del perfil completo
    embedding_gemelo: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Razón de regeneración
    razon_regeneracion: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (sa.UniqueConstraint("persona_id", "version"),)

    # Relaciones
    persona: Mapped["Persona"] = relationship("Persona", back_populates="gemelos")
    corpus_uso: Mapped[list["GemeloCorpusUso"]] = relationship(
        "GemeloCorpusUso", back_populates="gemelo", cascade="all, delete-orphan"
    )
    respuestas_simulacion: Mapped[list["RespuestaSimulacion"]] = relationship(
        "RespuestaSimulacion", back_populates="gemelo"
    )


class GemeloCorpusUso(Base):
    """Linaje: qué papers y documentos se usaron para generar un gemelo específico."""

    __tablename__ = "gemelo_corpus_uso"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gemelo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("gemelo.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("paper.id", ondelete="SET NULL"),
        nullable=True,
    )
    documento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("documento_corpus.id", ondelete="SET NULL"),
        nullable=True,
    )
    longitud_usada: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    posicion_orden: Mapped[int | None] = mapped_column(sa.SmallInteger, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "(paper_id IS NOT NULL AND documento_id IS NULL) OR "
            "(paper_id IS NULL AND documento_id IS NOT NULL)",
            name="ck_gemelo_corpus_uso_exclusivo",
        ),
    )

    # Relaciones
    gemelo: Mapped["Gemelo"] = relationship("Gemelo", back_populates="corpus_uso")
    paper: Mapped["Paper | None"] = relationship("Paper", back_populates="gemelo_corpus_usos")
    documento: Mapped["DocumentoCorpus | None"] = relationship(
        "DocumentoCorpus", back_populates="gemelo_corpus_usos"
    )
