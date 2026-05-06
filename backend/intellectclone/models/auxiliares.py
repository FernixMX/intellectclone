"""
Modelos SQLAlchemy: tablas auxiliares.
Tablas: ValidacionGemelo, ExportToken, ConfiguracionPresupuesto, ConsumoLlm, TemaTroncoComun

Estas tablas NO están en el SQL original; se crean en la primera migración de Alembic.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from intellectclone.db.base import Base

if TYPE_CHECKING:
    from intellectclone.models.gemelo import Gemelo
    from intellectclone.models.sistema import UsuarioSistema


class ValidacionGemelo(Base):
    """
    Registro de validaciones de gemelos por los propios investigadores retratados.
    Ver doc 07, sección 9.
    """

    __tablename__ = "validacion_gemelo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gemelo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("gemelo.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Resultado de la validación
    aprobado: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    comentarios: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Secciones con correcciones específicas (JSONB libre)
    # Ejemplo: {"hexaco": {"nivel_extraversion": "medio", ...}, "idiolecto": {...}}
    correcciones: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    gemelo: Mapped["Gemelo"] = relationship("Gemelo")
    usuario: Mapped["UsuarioSistema"] = relationship("UsuarioSistema")


class ExportToken(Base):
    """
    Tokens de acceso para la API de exportación Mirrorfish (/export/v1/*).
    Ver CHANGELOG_alcance_v1.
    """

    __tablename__ = "export_token"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Restricciones de acceso
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    expira_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    ultimo_uso: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    usos_total: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="SET NULL"),
        nullable=True,
    )

    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    creador: Mapped["UsuarioSistema | None"] = relationship("UsuarioSistema")


class ConfiguracionPresupuesto(Base):
    """
    Configuración global de presupuesto LLM y alertas.
    Ver doc 08.
    """

    __tablename__ = "configuracion_presupuesto"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clave: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    valor_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    editor: Mapped["UsuarioSistema | None"] = relationship("UsuarioSistema")


class ConsumoLlm(Base):
    """
    Registro de consumo real de tokens por operación LLM.
    Ver doc 08 (seguimiento de presupuesto por usuario/operación).
    """

    __tablename__ = "consumo_llm"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="SET NULL"),
        nullable=True,
    )
    operacion: Mapped[str] = mapped_column(
        sa.String(100), nullable=False
    )  # 'perfilador' | 'simulacion' | 'embedding'
    modelo: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    tokens_prompt: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    tokens_completion: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    tokens_total: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    costo_usd: Mapped[float] = mapped_column(sa.Numeric(10, 6), nullable=False, default=0)

    # Referencia a la entidad que generó el consumo (polimórfica vía JSONB)
    entidad_tipo: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    entidad_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    usuario: Mapped["UsuarioSistema | None"] = relationship("UsuarioSistema")


class TemaTroncoComun(Base):
    """
    Los 18 temas institucionales del tronco común UAT para posturas temáticas.
    Catálogo de referencia para el perfilador al asignar posturas.
    """

    __tablename__ = "tema_tronco_comun"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clave: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    categoria: Mapped[str | None] = mapped_column(
        sa.String(100), nullable=True
    )  # agrupación de temas
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    orden: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
