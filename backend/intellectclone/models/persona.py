"""
Modelos SQLAlchemy: personas y sus relaciones institucionales.
Tablas: Persona, PersonaArea, PersonaDependenciaHistorico
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from intellectclone.db.base import Base
from intellectclone.models.enums import NivelSnii, TipoFuente, TipoPersona

if TYPE_CHECKING:
    from intellectclone.models.gemelo import Gemelo
    from intellectclone.models.institucional import AreaConocimiento, CuerpoAcademico, Dependencia
    from intellectclone.models.produccion import DocumentoCorpus, Paper
    from intellectclone.models.sistema import UsuarioSistema


class Persona(Base):
    """Miembro de la comunidad académica UAT (persona real, identificable)."""

    __tablename__ = "persona"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identidad básica
    nombre_completo: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    primer_nombre: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    apellido_paterno: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    apellido_materno: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    # Tipo de membresía
    tipo: Mapped[TipoPersona] = mapped_column(
        sa.Enum(TipoPersona, name="tipo_persona", create_type=False),
        nullable=False,
        default=TipoPersona.investigador,
    )

    # Identificadores externos
    orcid: Mapped[str | None] = mapped_column(sa.String(19), unique=True, nullable=True)
    openalex_id: Mapped[str | None] = mapped_column(
        sa.String(50), unique=True, nullable=True
    )
    scopus_id: Mapped[str | None] = mapped_column(
        sa.String(50), unique=True, nullable=True
    )
    cvu_conacyt: Mapped[str | None] = mapped_column(
        sa.String(20), unique=True, nullable=True
    )
    google_scholar_id: Mapped[str | None] = mapped_column(
        sa.String(50), nullable=True
    )

    # Pertenencia institucional actual
    dependencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("dependencia.id", ondelete="SET NULL"),
        nullable=True,
    )
    cuerpo_academico_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("cuerpo_academico.id", ondelete="SET NULL"),
        nullable=True,
    )
    cargo: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    # Estatus académico
    nivel_snii: Mapped[NivelSnii | None] = mapped_column(
        sa.Enum(NivelSnii, name="nivel_snii", create_type=False),
        nullable=True,
    )
    snii_vigente_hasta: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    grado_maximo: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    grado_disciplina: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    # Métricas bibliométricas
    total_publicaciones: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    total_citas: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    indice_h: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    indice_i10: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    primera_publicacion: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    ultima_publicacion: Mapped[date | None] = mapped_column(sa.Date, nullable=True)

    # Datos de contacto público
    email_publico: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    sitio_web: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    # Estado en el sistema
    activa: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    motivo_baja: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    fecha_baja: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    # Trazabilidad de origen
    fuente_principal: Mapped[TipoFuente | None] = mapped_column(
        sa.Enum(TipoFuente, name="tipo_fuente", create_type=False),
        nullable=True,
    )

    # Embedding semántico del perfil
    embedding_perfil: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )

    # Metadatos extensibles
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
    dependencia: Mapped["Dependencia | None"] = relationship(
        "Dependencia", back_populates="personas", foreign_keys=[dependencia_id]
    )
    cuerpo_academico: Mapped["CuerpoAcademico | None"] = relationship(
        "CuerpoAcademico",
        back_populates="personas",
        foreign_keys=[cuerpo_academico_id],
    )
    areas: Mapped[list["PersonaArea"]] = relationship(
        "PersonaArea", back_populates="persona", cascade="all, delete-orphan"
    )
    historico_dependencias: Mapped[list["PersonaDependenciaHistorico"]] = relationship(
        "PersonaDependenciaHistorico", back_populates="persona", cascade="all, delete-orphan"
    )
    gemelos: Mapped[list["Gemelo"]] = relationship(
        "Gemelo", back_populates="persona", cascade="all, delete-orphan"
    )
    documentos_corpus: Mapped[list["DocumentoCorpus"]] = relationship(
        "DocumentoCorpus", back_populates="persona", cascade="all, delete-orphan"
    )
    usuario_sistema: Mapped["UsuarioSistema | None"] = relationship(
        "UsuarioSistema", back_populates="persona"
    )


class PersonaArea(Base):
    """Relación muchos-a-muchos: persona ↔ área de conocimiento con peso."""

    __tablename__ = "persona_area"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("area_conocimiento.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    peso: Mapped[float] = mapped_column(
        sa.Numeric(4, 3), nullable=False, default=1.0
    )
    fuente: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    paper_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    persona: Mapped["Persona"] = relationship("Persona", back_populates="areas")
    area: Mapped["AreaConocimiento"] = relationship("AreaConocimiento")


class PersonaDependenciaHistorico(Base):
    """Histórico de afiliaciones institucionales de una persona."""

    __tablename__ = "persona_dependencia_historico"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("dependencia.id", ondelete="SET NULL"),
        nullable=True,
    )
    cargo: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    es_actual: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    fuente: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    confianza: Mapped[float | None] = mapped_column(sa.Numeric(4, 3), nullable=True)
    metadatos: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    persona: Mapped["Persona"] = relationship(
        "Persona", back_populates="historico_dependencias"
    )
    dependencia: Mapped["Dependencia | None"] = relationship("Dependencia")
