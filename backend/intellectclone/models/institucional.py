"""
Modelos SQLAlchemy: estructura institucional de la UAT.
Tablas: Dependencia, CuerpoAcademico, AreaConocimiento
"""

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from intellectclone.db.base import Base

if TYPE_CHECKING:
    from intellectclone.models.persona import Persona


class Dependencia(Base):
    """Facultades, unidades académicas, centros y secretarías de la UAT."""

    __tablename__ = "dependencia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    nombre_corto: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    tipo: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    campus: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    sitio_web: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    activa: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    personas: Mapped[list["Persona"]] = relationship(
        "Persona", back_populates="dependencia", foreign_keys="Persona.dependencia_id"
    )
    cuerpos_academicos: Mapped[list["CuerpoAcademico"]] = relationship(
        "CuerpoAcademico", back_populates="dependencia"
    )


class CuerpoAcademico(Base):
    """Cuerpos académicos UAT (consolidado, en consolidación, en formación)."""

    __tablename__ = "cuerpo_academico"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str | None] = mapped_column(sa.String(50), unique=True, nullable=True)
    nombre: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    estatus: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    dependencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("dependencia.id", ondelete="SET NULL"),
        nullable=True,
    )
    lineas_generacion: Mapped[list[str] | None] = mapped_column(sa.ARRAY(sa.Text), nullable=True)
    fecha_registro: Mapped[sa.Date | None] = mapped_column(sa.Date, nullable=True)
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    dependencia: Mapped["Dependencia | None"] = relationship(
        "Dependencia", back_populates="cuerpos_academicos"
    )
    personas: Mapped[list["Persona"]] = relationship(
        "Persona",
        back_populates="cuerpo_academico",
        foreign_keys="Persona.cuerpo_academico_id",
    )


class AreaConocimiento(Base):
    """Taxonomía de áreas de conocimiento (CONACYT/SNII, OECD Fields of Science)."""

    __tablename__ = "area_conocimiento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    nivel: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("area_conocimiento.id", ondelete="SET NULL"),
        nullable=True,
    )
    sistema_origen: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Auto-relación jerárquica
    parent: Mapped["AreaConocimiento | None"] = relationship(
        "AreaConocimiento", back_populates="hijos", remote_side="AreaConocimiento.id"
    )
    hijos: Mapped[list["AreaConocimiento"]] = relationship(
        "AreaConocimiento", back_populates="parent"
    )
