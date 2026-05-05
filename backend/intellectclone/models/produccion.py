"""
Modelos SQLAlchemy: producción académica.
Tablas: Paper, Coautoria, DocumentoCorpus
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
from intellectclone.models.enums import (
    EstadoDocumento,
    TipoDocumentoCorpus,
    TipoPaper,
    TipoFuente,
)

if TYPE_CHECKING:
    from intellectclone.models.gemelo import GemeloCorpusUso
    from intellectclone.models.persona import Persona
    from intellectclone.models.sistema import Cosecha


class Paper(Base):
    """Publicación académica indexada."""

    __tablename__ = "paper"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identificadores únicos
    doi: Mapped[str | None] = mapped_column(sa.String(255), unique=True, nullable=True)
    openalex_id: Mapped[str | None] = mapped_column(
        sa.String(50), unique=True, nullable=True
    )
    handle_riuat: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    # Tipo
    tipo: Mapped[TipoPaper] = mapped_column(
        sa.Enum(TipoPaper, name="tipo_paper", create_type=False),
        nullable=False,
        default=TipoPaper.articulo,
    )

    # Datos bibliográficos
    titulo: Mapped[str] = mapped_column(sa.Text, nullable=False)
    titulo_normalizado: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    abstract_texto: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    año: Mapped[int | None] = mapped_column(sa.SmallInteger, nullable=True)
    fecha_publicacion: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    idioma: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)

    # Venue
    revista: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    issn: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    editorial: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    volumen: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    numero: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    paginas: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)

    # Acceso
    open_access: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    url_pdf: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    url_landing: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    license: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)

    # Citaciones
    total_citas: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    citas_por_año: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # type: ignore[type-arg]

    # Conceptos OpenAlex
    conceptos: Mapped[list[str] | None] = mapped_column(
        sa.ARRAY(sa.Text), nullable=True
    )

    # Embedding del título + abstract
    embedding_contenido: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )

    # Trazabilidad de cosecha
    fuente_origen: Mapped[TipoFuente | None] = mapped_column(
        sa.Enum(TipoFuente, name="tipo_fuente", create_type=False),
        nullable=True,
    )
    cosecha_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
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
    coautorias: Mapped[list["Coautoria"]] = relationship(
        "Coautoria", back_populates="paper", cascade="all, delete-orphan"
    )
    documentos_corpus: Mapped[list["DocumentoCorpus"]] = relationship(
        "DocumentoCorpus", back_populates="paper"
    )
    gemelo_corpus_usos: Mapped[list["GemeloCorpusUso"]] = relationship(
        "GemeloCorpusUso", back_populates="paper"
    )


class Coautoria(Base):
    """Relación muchos-a-muchos persona ↔ paper con metadatos de la coautoría."""

    __tablename__ = "coautoria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("paper.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Posición en la lista de autores
    posicion: Mapped[int | None] = mapped_column(sa.SmallInteger, nullable=True)
    total_autores: Mapped[int | None] = mapped_column(sa.SmallInteger, nullable=True)

    # Roles
    es_autor_correspondiente: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    es_primer_autor: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    es_ultimo_autor: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )

    # Afiliación declarada en ese paper
    afiliacion_declarada: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Confianza en la asignación
    confianza_match: Mapped[float] = mapped_column(
        sa.Numeric(4, 3), nullable=False, default=1.0
    )
    metodo_match: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (sa.UniqueConstraint("persona_id", "paper_id"),)

    # Relaciones
    persona: Mapped["Persona"] = relationship("Persona")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="coautorias")


class DocumentoCorpus(Base):
    """Documentos auxiliares que alimentan al perfilador (no son papers indexados)."""

    __tablename__ = "documento_corpus"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("paper.id", ondelete="SET NULL"),
        nullable=True,
    )

    titulo: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    tipo: Mapped[TipoDocumentoCorpus] = mapped_column(
        sa.Enum(TipoDocumentoCorpus, name="tipo_documento_corpus", create_type=False),
        nullable=False,
    )
    estado: Mapped[EstadoDocumento] = mapped_column(
        sa.Enum(EstadoDocumento, name="estado_documento", create_type=False),
        nullable=False,
        default=EstadoDocumento.pendiente,
    )

    # Contenido
    texto_extraido: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    longitud_caracteres: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    longitud_tokens_aprox: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # Archivo original
    archivo_path: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    archivo_nombre: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    archivo_mime: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    archivo_tamano_bytes: Mapped[int | None] = mapped_column(sa.BigInteger, nullable=True)

    # Procesamiento
    procesado_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    error_procesamiento: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

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
    persona: Mapped["Persona"] = relationship(
        "Persona", back_populates="documentos_corpus"
    )
    paper: Mapped["Paper | None"] = relationship(
        "Paper", back_populates="documentos_corpus"
    )
    gemelo_corpus_usos: Mapped[list["GemeloCorpusUso"]] = relationship(
        "GemeloCorpusUso", back_populates="documento"
    )
